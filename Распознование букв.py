import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
from PIL import Image
import cv2
import numpy as np
import matplotlib.pyplot as plt        
from tensorflow import keras
from tensorflow.keras.layers import Dense, Flatten
import tensorflow as tf
import shutil
from skimage import transform as tr
import random
alf = "АИЙКЛМНОПРСБТУФХЦЧШЩЪЫВЬЭЮЯГДЕЁЖЗ"
# ищет минимальное количество изображений одной буквы
# и выравнивает в остальных папках колличество изображений
def balancing(path_train = "./Train/"):  
    min = len(os.listdir(path_train+str(1)))
    for num_folder in range(2, 34):
        if len(os.listdir(path_train+str(num_folder))) < min:
            min = len(os.listdir(path_train+str(num_folder)))
    for num_folder in os.listdir(path_train):
        for file_name in os.listdir(path_train+num_folder):
            if len(os.listdir(path_train+num_folder)) <= min:
                break
            os.remove(path_train+num_folder+"/"+file_name)

# заменяет прозрачный задний фон на белый
def make_background(path_to_default_image, file_name, folder_name, path_train = "./Train/"):
    image = plt.imread(path_to_default_image)
    trans_mask = image[:, :, 3] == 0
    image[trans_mask] = [255, 255, 255, 255]
    new_img = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    path = path_train + folder_name + "/" + file_name + ".jpeg"
    cv2.imwrite(path, new_img)

# сдвиги, делает из одного начального изображения, 4 новых
def shift(path_to_image, file_name, num_folder, path_train = "./Train/"):
    img = plt.imread(path_to_image)
    file_name = file_name.split(".")[0]
    arr_translation = [[15, -15], [-15, 15], [-15, -15], [15, 15]]
    arr_caption=['15-15','-1515','-15-15','1515']
    for num_file in range(4):
        transform = tr.AffineTransform(translation=tuple(arr_translation[num_file]))
        warp_image = tr.warp(img, transform, mode="wrap")
        img_convert = cv2.convertScaleAbs(warp_image,alpha=(255.0))
        cv2.imwrite(path_train+num_folder+"/"+file_name+"."+str(num_file)+'.jpeg', img_convert)

# повороты, делает из одного начального изображения, 2 новых
def rotate(path_to_image, file_name, num_folder, path_train = "./Train/"):
    img = Image.open(path_to_image)
    file_name = file_name.split(".")[0]
    angles = np.ndarray((2,), buffer=np.array([-13, 13]), dtype=int)
    num_file = 1
    for angle in angles:
        transformed_image = tr.rotate(np.array(img),
                                      angle,
                                      cval=255,
                                      preserve_range=True).astype(np.uint8)
        cv2.imwrite(path_train+num_folder+"/"+file_name+"r"+str(num_file)+'.jpeg', transformed_image)
        num_file += 1

# создаёт папку с изображениями для проверки , по умолчанию берёт 10% от всех изображений
def create_validation(k = 10, path_train = "./Train/", path_val = "./Validation"):
    size = len(os.listdir(path_train+"1"))
    count = size * k // 100
    try:
        shutil.rmtree(path_val)
    except:
        pass
    os.mkdir(path_val)
    for folder_name in os.listdir(path_train):
        os.mkdir(path_val+"/"+folder_name)
        x = 1
        for replace_file in random.sample(sorted(os.listdir(path_train+folder_name)), count):
            shutil.move(path_train+folder_name+"/"+replace_file, path_val+"/"+folder_name+"/"+replace_file)
            x += 1

# создаёт и обучает модель
def create_model(TRAINING_DIR = "./Train", VALIDATION_DIR = "./Validation"):
    ImageDataGenerator = tf.keras.preprocessing.image.ImageDataGenerator
    train_datagen = ImageDataGenerator(rescale=1.0 / 255.)
    train_generator = train_datagen.flow_from_directory(TRAINING_DIR,
                                                        batch_size=40,
                                                        class_mode='binary',
                                                        target_size=(278,278))

    validation_datagen = ImageDataGenerator(rescale=1.0 / 255.)
    validation_generator = validation_datagen.flow_from_directory(VALIDATION_DIR,
                                                                  batch_size=40,
                                                                  class_mode='binary',
                                                                  target_size=(278,278))

    model = tf.keras.models.Sequential([
        tf.keras.layers.Conv2D(16, (3, 3), activation='relu',
                               input_shape=(278,278, 3)),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(512, activation='relu'),
        tf.keras.layers.Dense(33, activation='softmax')
    ])
    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    #model.summary()
    model.fit(train_generator,
              epochs=2,
              verbose=2,
              validation_data=validation_generator)
    try:
        shutil.rmtree('model_bkv5')
    except:
        pass
    model.save('model_bkv5')

# создаёт базу для обучения
def create_dataset(path_train = "./Train/", path_to_default_image = "./Cyrillic/"):
    try:
        shutil.rmtree(path_train)
    except:
        pass
    os.mkdir(path_train)
    num_of_folder = 1
    for name_of_folder in alf:
        num_of_img = 1
        os.mkdir(path_train + str(num_of_folder))
        for name_of_img in os.listdir(path_to_default_image + name_of_folder):
            make_background(path_to_default_image + name_of_folder + "/" + name_of_img,
                            str(num_of_img),
                            str(num_of_folder))
            num_of_img += 1
        num_of_folder += 1
    for num_of_folder in os.listdir(path_train):
        for num_of_img in os.listdir(path_train + num_of_folder):
            shift(path_train + num_of_folder + "/" + num_of_img,
                  num_of_img,
                  num_of_folder)
            rotate(path_train + num_of_folder + "/" + num_of_img,
                   num_of_img,
                   num_of_folder)
    balancing()
    create_validation()

#Перевод изображения в чб
def convert(path_to_img):
    color_image = Image.open(path_to_img)
    bw = color_image.convert('L')
    


# распознование
def predicting(path_to_image):
    image = keras.preprocessing.image
    model = keras.models.load_model('model_bkv4')
    
    img = image.load_img(path_to_image,
                         target_size=(278, 278))
    thresh = 200
    fn = lambda x : 255 if x > thresh else 0
    img = img.convert('L').point(fn, mode='1')
    img = img.convert('RGB')
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    images = np.vstack([x])
    classes = model.predict(images, batch_size=1)
    result = int(np.argmax(classes))
    return alf[result]

def letters_extract(image_file: str, out_size=278):
    img = cv2.imread(image_file)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)
    img_erode = cv2.erode(thresh, np.ones((3, 3), np.uint8), iterations=1)

    contours, hierarchy = cv2.findContours(img_erode, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    output = img.copy()

    letters = []
    for idx, contour in enumerate(contours):
        (x, y, w, h) = cv2.boundingRect(contour)
        if hierarchy[0][idx][3] == 0:
            cv2.rectangle(output, (x, y), (x + w, y + h), (70, 0, 0), 1)
            letter_crop = gray[y:y + h, x:x + w]

            size_max = max(w, h)
            letter_square = 255 * np.ones(shape=[size_max, size_max], dtype=np.uint8)
            if w > h:

                y_pos = size_max//2 - h//2
                letter_square[y_pos:y_pos + h, 0:w] = letter_crop
            elif w < h:

                x_pos = size_max//2 - w//2
                letter_square[0:h, x_pos:x_pos + w] = letter_crop
            else:
                letter_square = letter_crop

            letters.append((x, w, cv2.resize(letter_square, (out_size, out_size), interpolation=cv2.INTER_AREA)))

    letters.sort(key=lambda x: x[0], reverse=False)
    for i in range(len(letters)):
        cv2.imwrite('lettter'+str(i), letters[i][2]) 




if __name__ == '__main__':
    letters_extract(r"3.jpg")
