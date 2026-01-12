import serial
import cv2
import numpy as np
import joblib
import time

def detectar_camara(max_index=10):
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cap.release()
            return i
        cap.release()
    return None

indice_camara = detectar_camara()
if indice_camara is None:
    print("No se detectó ninguna cámara.")
    exit()

cap = cv2.VideoCapture(indice_camara)

# Cargar modelo KNN
modelo_path = 'C:/Users/KEVIN/Desktop/UNIVERSIDAD/9 semestre/Flexibles/banda ultimo cort/modelo_knn_colores.pkl'
knn = joblib.load(modelo_path)

# Configura el puerto serial
ser = serial.Serial('COM3', 115200, timeout=1)
ser.flush()

if not cap.isOpened():
    print("No se pudo abrir la cámara")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 15)

ultimo_color = None
color_buffer = []
tolerancia = 4  # Cuántos cuadros iguales se necesitan para aceptar el color
bins = 16  # Número de bins para el histograma HSV

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Calcular histogramas para cada canal HSV
    hist_h = cv2.calcHist([hsv], [0], None, [bins], [0, 180])
    hist_s = cv2.calcHist([hsv], [1], None, [bins], [0, 256])
    hist_v = cv2.calcHist([hsv], [2], None, [bins], [0, 256])

    # Normalizar histogramas
    hist_h = cv2.normalize(hist_h, hist_h).flatten()
    hist_s = cv2.normalize(hist_s, hist_s).flatten()
    hist_v = cv2.normalize(hist_v, hist_v).flatten()

    # Concatenar en vector de características
    features = np.concatenate([hist_h, hist_s, hist_v])

    try:
        color_predicho = knn.predict([features])[0].strip().capitalize()
        color_buffer.append(color_predicho)

        if len(color_buffer) > tolerancia:
            color_buffer.pop(0)

        if len(color_buffer) == tolerancia:
            if color_buffer.count(color_buffer[0]) == len(color_buffer) and color_buffer[0] != ultimo_color:
                ultimo_color = color_buffer[0]
                print(f"Color detectado por KNN: {ultimo_color}")
                ser.write((ultimo_color + '\n').encode('utf-8'))

    except Exception as e:
        print("Error de predicción:", e)

    time.sleep(0.2)  # Evita sobrecargar el CPU