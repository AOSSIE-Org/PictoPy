"""
Manual verification script for face alignment feature.

Run this to test face alignment without pytest.
"""

import sys
import cv2
import numpy as np
from app.utils.face_alignment import align_face_simple, simple_face_crop
from app.config import settings

def create_test_image():
    """Create a test image with a tilted face pattern."""
    img = np.ones((400, 400, 3), dtype=np.uint8) * 200
    
    # Draw a simple "face" with tilted features
    center = (200, 200)
    # Face outline
    cv2.ellipse(img, center, (80, 100), 15, 0, 360, (255, 255, 255), -1)
    # Eyes (tilted)
    cv2.circle(img, (170, 180), 10, (0, 0, 0), -1)
    cv2.circle(img, (230, 195), 10, (0, 0, 0), -1)
    # Nose
    cv2.line(img, (200, 200), (195, 230), (100, 100, 100), 2)
    # Mouth (tilted)
    cv2.ellipse(img, (200, 250), (30, 15), 15, 0, 180, (0, 0, 0), 2)
    
    return img

def test_alignment_disabled():
    """Test alignment when disabled."""
    print("Test 1: Alignment disabled...")
    
    img = create_test_image()
    bbox = {"x": 100, "y": 100, "width": 200, "height": 200}
    
    # Temporarily disable
    original_setting = settings.FACE_ALIGNMENT_ENABLED
    settings.FACE_ALIGNMENT_ENABLED = False
    
    result = align_face_simple(img, bbox, padding=20)
    expected = simple_face_crop(img, bbox, padding=20)
    
    settings.FACE_ALIGNMENT_ENABLED = original_setting
    
    if result.shape == expected.shape:
        print("✓ PASS: Returns simple crop when disabled")
        return True
    else:
        print("✗ FAIL: Unexpected result shape")
        return False

def test_alignment_enabled():
    """Test alignment when enabled."""
    print("\\nTest 2: Alignment enabled...")
    
    img = create_test_image()
    bbox = {"x": 100, "y": 100, "width": 200, "height": 200}
    
    # Enable alignment
    original_setting = settings.FACE_ALIGNMENT_ENABLED
    settings.FACE_ALIGNMENT_ENABLED = True
    
    try:
        result = align_face_simple(img, bbox, padding=20)
        settings.FACE_ALIGNMENT_ENABLED = original_setting
        
        if result is not None and result.shape[0] > 0 and result.shape[1] > 0:
            print("✓ PASS: Returns valid aligned image")
            return True
        else:
            print("✗ FAIL: Invalid result")
            return False
    except Exception as e:
        settings.FACE_ALIGNMENT_ENABLED = original_setting
        print(f"✗ FAIL: Exception raised: {e}")
        return False

def test_edge_cases():
    """Test edge cases."""
    print("\\nTest 3: Edge cases...")
    
    original_setting = settings.FACE_ALIGNMENT_ENABLED
    settings.FACE_ALIGNMENT_ENABLED = True
    
    passed = 0
    total = 0
    
    # Test 1: Small image
    total += 1
    try:
        tiny_img = np.zeros((50, 50, 3), dtype=np.uint8)
        result = align_face_simple(tiny_img, {"x": 10, "y": 10, "width": 20, "height": 20}, padding=5)
        if result is not None:
            passed += 1
            print("  ✓ Small image handled")
        else:
            print("  ✗ Small image failed")
    except:
        print("  ✗ Small image raised exception")
    
    # Test 2: Boundary bbox
    total += 1
    try:
        img = create_test_image()
        result = align_face_simple(img, {"x": 350, "y": 350, "width": 100, "height": 100}, padding=20)
        if result is not None and result.shape[0] > 0:
            passed += 1
            print("  ✓ Boundary bbox handled")
        else:
            print("  ✗ Boundary bbox failed")
    except:
        print("  ✗ Boundary bbox raised exception")
    
    # Test 3: Different paddings
    total += 1
    try:
        img = create_test_image()
        for padding in [0, 10, 20, 50]:
            result = align_face_simple(img, {"x": 100, "y": 100, "width": 150, "height": 150}, padding=padding)
            if result is None or result.shape[0] == 0:
                raise ValueError(f"Failed at padding={padding}")
        passed += 1
        print("  ✓ Different paddings handled")
    except Exception as e:
        print(f"  ✗ Different paddings failed: {e}")
    
    settings.FACE_ALIGNMENT_ENABLED = original_setting
    
    print(f"\\nEdge cases: {passed}/{total} passed")
    return passed == total

def test_integration():
    """Test integration with FaceDetector."""
    print("\\nTest 4: Integration test...")
    
    try:
        from app.models.FaceDetector import FaceDetector
        
        # This should not raise an error just from import
        print("✓ PASS: FaceDetector imports successfully with alignment")
        return True
    except Exception as e:
        print(f"✗ FAIL: FaceDetector import failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("="*60)
    print("Face Alignment Manual Verification")
    print("="*60)
    
    results = []
    
    results.append(("Alignment disabled", test_alignment_disabled()))
    results.append(("Alignment enabled", test_alignment_enabled()))
    results.append(("Edge cases", test_edge_cases()))
    results.append(("Integration", test_integration()))
    
    print("\\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\\n✓ All tests passed! Face alignment is working correctly.")
        return 0
    else:
        print("\\n✗ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
