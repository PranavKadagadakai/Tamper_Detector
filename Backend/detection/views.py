from pathlib import Path
import os
import tempfile
import mimetypes
from datetime import datetime
from io import BytesIO

import numpy as np
import cv2
from PIL import Image, ImageChops, ImageFilter
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_bytes
import pytesseract
import exifread
import joblib

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UploadHistory
from .serializers import UploadSerializer, HistorySerializer, RegisterSerializer

# Optional if using SSIM for future improvements
# from skimage.metrics import structural_similarity as ssim


# === Constants ===
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = os.path.join(BASE_DIR, "detection", "model", "id_classifier.pkl")

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            if User.objects.filter(username=serializer.validated_data['username']).exists():
                return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        
        if not username or not password:
            return Response({"error": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)
            
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user_id": user.id,
                "username": user.username
            })
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class UploadImageView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uploaded_file = request.FILES.get('image')

        serializer = UploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
        if uploaded_file is None or uploaded_file.content_type not in allowed_types:
            return Response({"error": "Unsupported or missing file type"}, status=400)

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[-1]) as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            # If PDF, convert to image
            if uploaded_file.content_type == 'application/pdf':
                password = request.data.get("password", "").strip()

                # Check if password protected
                with open(tmp_path, 'rb') as f:
                    reader = PdfReader(f)
                    if reader.is_encrypted:
                        if not password:
                            return Response({"error": "PDF is password-protected. Please provide the password."}, status=400)

                        try:
                            reader.decrypt(password)
                        except Exception:
                            return Response({"error": "Incorrect PDF password."}, status=400)

                        # Decrypt and write to temp file
                        writer = PdfWriter()
                        for page in reader.pages:
                            writer.add_page(page)

                        decrypted_path = tmp_path + "_decrypted.pdf"
                        with open(decrypted_path, 'wb') as out:
                            writer.write(out)
                        os.unlink(tmp_path)
                        tmp_path = decrypted_path

                # Convert to image
                images = convert_from_bytes(open(tmp_path, 'rb').read())
                if not images:
                    return Response({"error": "Unable to convert PDF to image"}, status=400)

                img_path = tmp_path + "_page.jpg"
                images[0].save(img_path, 'JPEG')
                os.unlink(tmp_path)
                tmp_path = img_path


            results = self.detect_tampering(tmp_path)

            # Save to history if user is authenticated
            if request.user and request.user.is_authenticated:
                UploadHistory.objects.create(
                    user=request.user,
                    image=uploaded_file,
                    result="Original" if results['is_authentic'] else "Tampered",
                    confidence=results['confidence'],
                    detection_details=results
                )

            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

            return Response({
                "status": "Original" if results['is_authentic'] else "Tampered",
                "confidence": results['confidence'],
                "file_name": uploaded_file.name,
                "timestamp": datetime.now().isoformat(),
                "details": results
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # === ALL detection functions below ===

    def detect_tampering(self, image_path):
        results = {
            'is_authentic': True,
            'confidence': 100.0,
            'checks': {},
            'reasons': []
        }

        try:
            # 1. Basic image props
            img = Image.open(image_path)
            results['checks']['image_properties'] = {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode
            }

            # 2. EXIF Metadata
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, stop_tag='UNDEF', details=False)
            has_exif = bool(tags)
            results['checks']['exif_metadata'] = {
                'exists': has_exif,
                'count': len(tags),
                'software_used': str(tags.get('Software', 'None')),
                'creation_date': str(tags.get('DateTimeOriginal', 'None'))
            }

            if not has_exif:
                results['reasons'].append("Missing EXIF metadata (may be expected for government PDFs)")
                # Don't reduce confidence much for Aadhaar

            # 3. ELA
            ela = self.error_level_analysis(image_path)
            results['checks']['error_level_analysis'] = ela
            if ela['tamper_indication'] and ela['difference_mean'] > 20:
                results['confidence'] -= 10
                results['reasons'].append("High ELA difference indicates possible tampering")

            # 4. Copy-move
            copy_move = self.detect_copy_move(image_path)
            results['checks']['copy_move_detection'] = copy_move
            if copy_move['has_copy_move'] and copy_move['keypoints'] > 1200:
                results['confidence'] -= 15
                results['reasons'].append("Potential copy-move forgery (many keypoints matched)")

            # 5. Text check
            text_check = self.check_text_consistency(image_path)
            results['checks']['text_analysis'] = text_check
            if text_check['inconsistencies']:
                results['confidence'] -= 10
                results['reasons'].append("Text inconsistencies detected")

            # 6. Noise analysis
            noise = self.analyze_noise_patterns(image_path)
            results['checks']['noise_analysis'] = noise
            if noise['std_dev'] > 25:
                results['confidence'] -= 5
                results['reasons'].append("Unusual noise pattern")

            # 7. Compression
            compression = self.check_compression(image_path)
            results['checks']['compression_analysis'] = compression
            # No penalty if multiple compression is found — expected in downloads

            # 8. Edge consistency
            edges = self.check_edge_consistency(image_path)
            results['checks']['edge_analysis'] = edges
            if edges['inconsistent_edges']:
                results['confidence'] -= 5
                results['reasons'].append("Irregular edge patterns detected")
            
            # Feature vector for classification
            features = [
                1 if has_exif else 0,
                ela.get('difference_mean', 0),
                copy_move.get('keypoints', 0),
                noise.get('std_dev', 0),
                1 if edges.get('inconsistent_edges') else 0,
            ]

            label, prob = self.classify_with_model(features)

            results['checks']['ml_classification'] = {
                'label': ['Aadhaar', 'PAN', 'Tampered'][label],
                'confidence': round(float(prob)*100, 2)
            }

            # If ML thinks it's tampered → override
            if label == 2 and prob > 0.8:
                results['is_authentic'] = False
                results['confidence'] = round(float(prob)*100, 2)
                results['reasons'].append("ML model classified as tampered")

            # Final threshold
            results['confidence'] = round(max(0, min(100, results['confidence'])), 2)
            results['is_authentic'] = results['confidence'] >= 60

        except Exception as e:
            results['error'] = str(e)
            results['is_authentic'] = False
            results['confidence'] = 0
            results['reasons'].append("Internal error during detection")

        return results

    def error_level_analysis(self, image_path, quality=90):
        try:
            original = Image.open(image_path).convert('RGB')
            ela_path = os.path.join(tempfile.gettempdir(), 'ela_tmp.jpg')
            original.save(ela_path, 'JPEG', quality=quality)

            ela_image = cv2.absdiff(
                cv2.imread(image_path),
                cv2.imread(ela_path)
            )
            diff_mean = float(ela_image.mean())

            os.unlink(ela_path)
            return {
                'tamper_indication': diff_mean > 10,
                'difference_mean': diff_mean,
                'threshold': 10
            }
        except Exception as e:
            return {'error': str(e), 'tamper_indication': False}

    def detect_copy_move(self, image_path):
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            sift = cv2.SIFT_create()
            kp, des = sift.detectAndCompute(gray, None)
            return {
                'keypoints': len(kp),
                'has_copy_move': len(kp) > 500  # arbitrary threshold
            }
        except Exception as e:
            return {'error': str(e), 'has_copy_move': False}

    def check_text_consistency(self, image_path):
        try:
            text = pytesseract.image_to_string(Image.open(image_path))
            lines = text.split('\n')
            inconsistencies = any(len(line.strip()) < 3 for line in lines if line.strip())
            return {
                'ocr_text_sample': lines[:5],
                'inconsistencies': inconsistencies
            }
        except Exception as e:
            return {'error': str(e), 'inconsistencies': False}

    def analyze_noise_patterns(self, image_path):
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            blur = cv2.GaussianBlur(img, (5, 5), 0)
            noise = cv2.absdiff(img, blur)
            std_dev = np.std(noise)
            return {
                'std_dev': float(std_dev),
                'inconsistent_noise': std_dev > 10  # threshold
            }
        except Exception as e:
            return {'error': str(e), 'inconsistent_noise': False}

    def check_compression(self, image_path):
        try:
            file_type = mimetypes.guess_type(image_path)[0]
            return {
                'format': file_type,
                'multiple_compression': 'jpeg' in file_type
            }
        except Exception as e:
            return {'error': str(e), 'multiple_compression': False}

    def check_edge_consistency(self, image_path):
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            edges = cv2.Canny(img, 100, 200)
            edge_sum = np.sum(edges) / 255
            return {
                'edge_pixel_count': int(edge_sum),
                'inconsistent_edges': edge_sum < 1000  # threshold
            }
        except Exception as e:
            return {'error': str(e), 'inconsistent_edges': False}
    
    def classify_with_model(self, features):
        model = joblib.load(MODEL_PATH)
        label = model.predict([features])[0]
        prob = model.predict_proba([features])[0].max()
        return label, prob

class HistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        uploads = UploadHistory.objects.filter(user=request.user).order_by('-timestamp')
        serializer = HistorySerializer(uploads, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)