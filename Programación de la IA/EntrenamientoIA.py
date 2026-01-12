import cv2
import numpy as np
import os
from sklearn.neighbors import KNeighborsClassifier
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score

# Ruta a tu dataset organizado en carpetas por color
dataset_dir = "C:/Users/KEVIN/Desktop/UNIVERSIDAD/9 semestre/Flexibles/banda ultimo cort/Colores2_augmented"

def is_image_file(filename):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    ext = os.path.splitext(filename)[1].lower()
    return ext in valid_extensions

def extract_features(image_path, bins=16):
    print(f"Cargando imagen: {image_path}")  # Debug: imprime la ruta
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {image_path}")

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Calcular histograma HSV para cada canal
    hist_h = cv2.calcHist([hsv], [0], None, [bins], [0, 180])
    hist_s = cv2.calcHist([hsv], [1], None, [bins], [0, 256])
    hist_v = cv2.calcHist([hsv], [2], None, [bins], [0, 256])

    # Normalizar histogramas
    hist_h = cv2.normalize(hist_h, hist_h).flatten()
    hist_s = cv2.normalize(hist_s, hist_s).flatten()
    hist_v = cv2.normalize(hist_v, hist_v).flatten()

    # Concatenar en vector de características
    feature_vector = np.concatenate([hist_h, hist_s, hist_v])

    return feature_vector.tolist()

X = []
y = []

for color_folder in os.listdir(dataset_dir):
    folder_path = os.path.join(dataset_dir, color_folder)
    if os.path.isdir(folder_path):
        for filename in os.listdir(folder_path):
            if not is_image_file(filename):
                continue
            filepath = os.path.join(folder_path, filename)
            try:
                features = extract_features(filepath)
                X.append(features)
                y.append(color_folder)
            except FileNotFoundError as e:
                print(e)

if len(X) == 0:
    raise ValueError("No se encontraron imágenes válidas para entrenar.")

print(f"Total muestras: {len(X)}")
print(f"Clases encontradas: {set(y)}")

# --- Buscar mejor k con validación cruzada ---
from sklearn.model_selection import cross_val_score
import numpy as np

k_values = range(1, 20, 2)  # valores impares de k
scores = []

print("Buscando mejor valor de k con validación cruzada...")
for k in k_values:
    knn = KNeighborsClassifier(n_neighbors=k)
    cv_scores = cross_val_score(knn, X, y, cv=5, scoring='accuracy')
    mean_score = cv_scores.mean()
    scores.append(mean_score)
    print(f"k={k}, Accuracy promedio CV: {mean_score:.4f}")

best_k = k_values[np.argmax(scores)]
print(f"Mejor k encontrado: {best_k}")

# Entrenar con mejor k encontrado
knn_final = KNeighborsClassifier(n_neighbors=best_k)
knn_final.fit(X, y)

# Dividir para evaluación final (opcional)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
y_pred = knn_final.predict(X_test)
print("Reporte de clasificación en conjunto de prueba:")
print(classification_report(y_test, y_pred))
print(f"Accuracy en conjunto de prueba: {accuracy_score(y_test, y_pred):.4f}")

# Guardar modelo entrenado
modelo_path = 'C:/Users/KEVIN/Desktop/UNIVERSIDAD/9 semestre/Flexibles/banda ultimo cort/modelo_knn_colores_mejor.pkl'
joblib.dump(knn_final, modelo_path)
print(f"Modelo KNN con k={best_k} entrenado y guardado en: {modelo_path}")

def predict_color(img, model=knn_final, bins=16):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    hist_h = cv2.calcHist([hsv], [0], None, [bins], [0, 180])
    hist_s = cv2.calcHist([hsv], [1], None, [bins], [0, 256])
    hist_v = cv2.calcHist([hsv], [2], None, [bins], [0, 256])

    hist_h = cv2.normalize(hist_h, hist_h).flatten()
    hist_s = cv2.normalize(hist_s, hist_s).flatten()
    hist_v = cv2.normalize(hist_v, hist_v).flatten()

    feature_vector = np.concatenate([hist_h, hist_s, hist_v])
    return model.predict([feature_vector])[0]

if __name__ == '__main__':
    test_img_path = 'C:/Users/KEVIN/Desktop/UNIVERSIDAD/9 semestre/Flexibles/banda ultimo cort/Colores2_augmented/Verde/1 (98)_aug2.jpeg'
    test_img = cv2.imread(test_img_path)
    if test_img is None:
        print(f"No se pudo cargar la imagen de prueba: {test_img_path}")
    else:
        pred = predict_color(test_img)
        print(f"Color predicho: {pred}")
