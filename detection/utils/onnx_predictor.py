import onnxruntime as ort
import numpy as np
from PIL import Image
import io

# Load ONNX model
onnx_session = ort.InferenceSession("detection/ai_models/ensemble_model_v1.0.0.onnx")

# Configuration
INPUT_SIZE = (224, 224)
EXPECTED_SHAPE = (1, 224, 224, 3)
INPUT_NAME = onnx_session.get_inputs()[0].name
LABELS = [
 'Apple__black_rot',
 'Apple__healthy',
 'Apple__rust',
 'Apple__scab',
 'Cassava__bacterial_blight',
 'Cassava__brown_streak_disease',
 'Cassava__green_mottle',
 'Cassava__healthy',
 'Cassava__mosaic_disease',
 'Cherry__healthy',
 'Cherry__powdery_mildew',
 'Chili__healthy',
 'Chili__leaf curl',
 'Chili__leaf spot',
 'Chili__whitefly',
 'Chili__yellowish',
 'Coffee__cercospora_leaf_spot',
 'Coffee__healthy',
 'Coffee__red_spider_mite',
 'Coffee__rust',
 'Corn__common_rust',
 'Corn__gray_leaf_spot',
 'Corn__healthy',
 'Corn__northern_leaf_blight',
 'Cucumber__diseased',
 'Cucumber__healthy',
 'Gauva__diseased',
 'Gauva__healthy',
 'Grape__black_measles',
 'Grape__black_rot',
 'Grape__healthy',
 'Grape__leaf_blight_(isariopsis_leaf_spot)',
 'Jamun__diseased',
 'Jamun__healthy',
 'Lemon__diseased',
 'Lemon__healthy',
 'Mango__diseased',
 'Mango__healthy',
 'Peach__bacterial_spot',
 'Peach__healthy',
 'Pepper_bell__bacterial_spot',
 'Pepper_bell__healthy',
 'Pomegranate__diseased',
 'Pomegranate__healthy',
 'Potato__early_blight',
 'Potato__healthy',
 'Potato__late_blight',
 'Rice__brown_spot',
 'Rice__healthy',
 'Rice__hispa',
 'Rice__leaf_blast',
 'Rice__neck_blast',
 'Soybean__bacterial_blight',
 'Soybean__caterpillar',
 'Soybean__diabrotica_speciosa',
 'Soybean__downy_mildew',
 'Soybean__healthy',
 'Soybean__mosaic_virus',
 'Soybean__powdery_mildew',
 'Soybean__rust',
 'Soybean__southern_blight',
 'Strawberry___leaf_scorch',
 'Strawberry__healthy',
 'Sugarcane__bacterial_blight',
 'Sugarcane__healthy',
 'Sugarcane__red_rot',
 'Sugarcane__red_stripe',
 'Sugarcane__rust',
 'Tea__algal_leaf',
 'Tea__anthracnose',
 'Tea__bird_eye_spot',
 'Tea__brown_blight',
 'Tea__healthy',
 'Tea__red_leaf_spot',
 'Tomato__bacterial_spot',
 'Tomato__early_blight',
 'Tomato__healthy',
 'Tomato__late_blight',
 'Tomato__leaf_mold',
 'Tomato__mosaic_virus',
 'Tomato__septoria_leaf_spot',
 'Tomato__spider_mites_(two_spotted_spider_mite)',
 'Tomato__target_spot',
 'Tomato__yellow_leaf_curl_virus',
 'Wheat__brown_rust',
 'Wheat__healthy',
 'Wheat__septoria',
 'Wheat__yellow_rust']




def is_preprocessed(image_array: np.ndarray) -> bool:
    """
    Checks if image is likely preprocessed:
    - shape (224, 224, 3)
    - dtype float32
    - values between 0 and 1
    """
    if image_array.shape == (224, 224, 3) and image_array.dtype == np.float32:
        min_val, max_val = image_array.min(), image_array.max()
        return 0.0 <= min_val <= 1.0 and max_val <= 1.0
    return False


def preprocess_image(image_file) -> np.ndarray:
    """
    Preprocesses the image to shape (1, 224, 224, 3) (NHWC).
    """
    try:
        image_file.seek(0)
        image = Image.open(image_file).convert("RGB")
        image_array = np.array(image)

        if is_preprocessed(image_array):
            # Already resized and normalized, just add batch dimension
            tensor = np.expand_dims(image_array, axis=0)  # (1, 224, 224, 3)
        else:
            # Resize, normalize, add batch dim
            image = image.resize(INPUT_SIZE)
            image_array = np.array(image).astype(np.float32) / 255.0  # (224, 224, 3)
            tensor = np.expand_dims(image_array, axis=0)  # (1, 224, 224, 3)

        if tensor.shape != EXPECTED_SHAPE:
            raise ValueError(f"Final input tensor has invalid shape: {tensor.shape}, expected {EXPECTED_SHAPE}")

        return tensor.astype(np.float32)

    except Exception as e:
        raise ValueError(f"Image preprocessing failed: {str(e)}")


def predict(image_file) -> dict:
    """
    Performs inference using the ONNX model with NHWC input.
    """
    try:
        input_tensor = preprocess_image(image_file)
        outputs = onnx_session.run(None, {INPUT_NAME: input_tensor})

        probabilities = outputs[0][0]  # (num_classes,)
        confidence = float(np.max(probabilities))
        predicted_index = int(np.argmax(probabilities))
        predicted_label = LABELS[predicted_index]

        return {
            "label": predicted_label,
            "confidence": round(confidence, 4)
        }
    except Exception as e:
        return {
            "error": str(e)
        }
