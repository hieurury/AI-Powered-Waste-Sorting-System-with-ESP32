import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
import os

# --- BASIC CONFIGURATION ---
DATASET_DIR = 'dataset'
IMG_SIZE = (224, 224)   # Standard input image size for MobileNetV2
BATCH_SIZE = 32         # Number of images processed in one batch
EPOCHS = 10             # Number of iterations over the entire dataset (can increase to 20-30 for better accuracy)

print("1. Preparing data...")
# Automatically split data: 80% for training, 20% for validation
# Also rescale pixel values to 0-1 range
datagen = ImageDataGenerator(validation_split=0.2, rescale=1./255)

train_generator = datagen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training'
)

val_generator = datagen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation'
)

# Save the list of class labels (e.g., {'metal': 0, 'paper': 1, 'plastic': 2})
class_indices = train_generator.class_indices
print(f"Class labels found: {class_indices}")

print("\n2. Initializing AI Model (MobileNetV2)...")
# Load MobileNetV2 base (exclude the default classification head - include_top=False)
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

# Freeze the pre-trained layers so they are not updated during training
base_model.trainable = False

# Build a new Classification Head for our 3 waste types
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.2)(x) # Prevent overfitting

# Output layer corresponding to the number of waste types (3 classes)
predictions = Dense(train_generator.num_classes, activation='softmax')(x)

# Combine base and new head into a complete model
model = Model(inputs=base_model.input, outputs=predictions)

# Compile the model
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

print("\n3. Starting training...")
history = model.fit(
    train_generator,
    epochs=EPOCHS,
    validation_data=val_generator
)

print("\n4. Saving model...")
# Export the AI model for server.py to use later
model.save('model.h5')
print("Done! Model saved successfully as: 'model.h5'")