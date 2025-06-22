from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UploadHistory
from .serializers import UploadSerializer, HistorySerializer, RegisterSerializer
import os
from datetime import datetime
from PIL import Image, ImageChops, ImageFilter
import numpy as np
from io import BytesIO
import cv2
import tempfile
import pytesseract
from skimage.metrics import structural_similarity as ssim
import exifread
import hashlib
import mimetypes

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

        allowed_types = ['image/jpeg', 'image/png']
        if uploaded_file is None or uploaded_file.content_type not in allowed_types:
            return Response({"error": "Unsupported or missing file type"}, status=400)

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            results = self.detect_tampering(tmp_path)

            if request.user.is_authenticated:
                UploadHistory.objects.create(
                    user=request.user,
                    image=uploaded_file,
                    result="Original" if results['is_authentic'] else "Tampered",
                    confidence=results['confidence'],
                    detection_details=results
                )

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

    def detect_tampering(self, image_path):
        """Comprehensive tamper detection function"""
        results = {
            'is_authentic': True,
            'confidence': 100.0,
            'checks': {}
        }

        try:
            # 1. Basic Image Properties Check
            img = Image.open(image_path)
            width, height = img.size
            results['checks']['image_properties'] = {
                'width': width,
                'height': height,
                'format': img.format,
                'mode': img.mode
            }

            # 2. EXIF Metadata Analysis
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
                results['checks']['exif_metadata'] = {
                    'exists': bool(tags),
                    'count': len(tags),
                    'software_used': str(tags.get('Software', 'None')),
                    'creation_date': str(tags.get('DateTimeOriginal', 'None'))
                }

            # 3. Error Level Analysis (ELA)
            ela_result = self.error_level_analysis(image_path)
            results['checks']['error_level_analysis'] = ela_result
            if ela_result['tamper_indication']:
                results['is_authentic'] = False
                results['confidence'] *= 0.7

            # 4. Copy-Move Detection
            copy_move_result = self.detect_copy_move(image_path)
            results['checks']['copy_move_detection'] = copy_move_result
            if copy_move_result['has_copy_move']:
                results['is_authentic'] = False
                results['confidence'] *= 0.6

            # 5. Text Consistency Check
            text_result = self.check_text_consistency(image_path)
            results['checks']['text_analysis'] = text_result
            if text_result['inconsistencies']:
                results['is_authentic'] = False
                results['confidence'] *= 0.8

            # 6. Noise Analysis
            noise_result = self.analyze_noise_patterns(image_path)
            results['checks']['noise_analysis'] = noise_result
            if noise_result['inconsistent_noise']:
                results['is_authentic'] = False
                results['confidence'] *= 0.75

            # 7. Compression Artifacts
            compression_result = self.check_compression(image_path)
            results['checks']['compression_analysis'] = compression_result
            if compression_result['multiple_compression']:
                results['is_authentic'] = False
                results['confidence'] *= 0.65

            # 8. Edge Inconsistency Detection
            edge_result = self.check_edge_consistency(image_path)
            results['checks']['edge_analysis'] = edge_result
            if edge_result['inconsistent_edges']:
                results['is_authentic'] = False
                results['confidence'] *= 0.7

            # Final confidence adjustment
            results['confidence'] = max(0, min(100, results['confidence']))

        except Exception as e:
            results['error'] = str(e)
            results['is_authentic'] = False
            results['confidence'] = 0

        return results

    def error_level_analysis(self, image_path, quality=90):
        """Detect inconsistencies through Error Level Analysis"""
        try:
            # Save at known quality level
            img = Image.open(image_path)
            tmp_ela_path = os.path.join(tempfile.gettempdir(), 'ela_temp.jpg')
            img.save(tmp_ela_path, 'JPEG', quality=quality)
            
            # Calculate difference
            original = cv2.imread(image_path)
            compressed = cv2.imread(tmp_ela_path)
            diff = cv2.absdiff(original, compressed)
            diff_mean = diff.mean()
            
            # Clean up
            os.unlink(tmp_ela_path)
            
            return {
                'tamper_indication': diff_mean > 10,  # Threshold
                'difference_mean': float(diff_mean),
                'threshold': 10
            }
        except Exception as e:
            return {'error': str(e), 'tamper_indication': False}

    def detect_copy_move(self, image_path, threshold=0.8):
        """Detect copy-move forgery using SIFT features"""
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Initialize SIFT detector
            sift = cv2.SIFT_create()
            kp, des = sift.detectAndCompute(gray, None)
            
            # FLANN parameters and matcher
            FLANN_INDEX_KDTREE = 1
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
        except Exception as e:
            return {'error': str(e), 'tamper_indication': False}

class HistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        uploads = UploadHistory.objects.filter(user=request.user).order_by('-timestamp')
        serializer = HistorySerializer(uploads, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)