import cv2
import numpy as np
import onnxruntime as ort

# Путь к ONNX-модели
MODEL_PATH = "anti-spoof-mn3.onnx"

# Загрузка модели ONNX
print("Загрузка модели...")
onnx_session = ort.InferenceSession(MODEL_PATH)
input_name = onnx_session.get_inputs()[0].name
output_name = onnx_session.get_outputs()[0].name
print("Модель загружена успешно!")

# Функция для предобработки изображения
def preprocess(image, input_size=(128, 128)):
    image = cv2.resize(image, input_size)  # Изменяем размер изображения
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.astype(np.float32) / 255.0  # Нормализация
    image = np.transpose(image, (2, 0, 1))  # HWC -> CHW
    image = np.expand_dims(image, axis=0)  # Добавление batch dimension
    return image

# Захват видео с веб-камеры
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Не удалось получить доступ к веб-камере")
    exit()

print("Начало захвата видео...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Ошибка чтения кадра")
        break

    # Предобработка кадра
    input_frame = preprocess(frame)

    # Прогон через модель
    predictions = onnx_session.run([output_name], {input_name: input_frame})[0]

    # Интерпретация результата
    probability_real = predictions[0][0]  # Вероятность, что лицо реальное
    probability_fake = 1 - probability_real  # Вероятность, что лицо поддельное

    label = "Real" if probability_real > 0.5 else "Fake"
    probability = probability_real if probability_real > 0.5 else probability_fake

    # Вывод результата на экран
    color = (0, 255, 0) if label == "Real" else (0, 0, 255)
    text = f"{label} ({probability:.2f})"  # Метка с вероятностью

    cv2.putText(frame, f"Anti-spoofing: {text}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.imshow("Anti-Spoofing Test", frame)

    # Выход по нажатию 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождение ресурсов
cap.release()
cv2.destroyAllWindows()
