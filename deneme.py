import pyautogui
import cv2
import numpy as np
import time
import keyboard
import threading

# Hedef resmin dosya yolunu belirleyin
target_image_path = 'muz.png'

# Hedef resmin okunması
target_image = cv2.imread(target_image_path)

# Hedef resmin koordinatlarını başlangıçta None olarak ayarlayın
target_position = None

# Hedef resmi tarama ve koordinatlarını kaydetme
while target_position is None:
    # Ekran görüntüsü alma
    screenshot = pyautogui.screenshot()
    screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Ekran görüntüsünde hedef resmi arama
    result = cv2.matchTemplate(screenshot, target_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Eşik değeri, hedef resmin bulunup bulunmadığını belirlemek için
    threshold = 0.8
    if max_val >= threshold:
        # Hedef resmin merkezi
        target_w = target_image.shape[1]
        target_h = target_image.shape[0]
        center_x = max_loc[0] + target_w // 2
        center_y = max_loc[1] + target_h // 2
        target_position = (center_x, center_y)
        print(f'Hedef konum bulundu: ({center_x}, {center_y})')

    # Kısa bir süre bekle ve tekrar dene
    time.sleep(0.5)

print("Tıklama işlemi başlıyor. Çıkmak için Ctrl+Q tuşlarına basın.")

# Tıklama işlemi fonksiyonu
def click_target(position):
    while True:
        if keyboard.is_pressed('ctrl+q'):
            print("Thread sonlandırıldı.")
            break

        if position is not None:
            # Tıklama işlemi
            pyautogui.click(position[0], position[1])
            print(f'Tıklama: ({position[0]}, {position[1]})')

            # Tıklamalar arasında bekleme süresi
            time.sleep(0.1)  # 0.1 saniye bekleme (ayarlanabilir)

# Thread listesi
threads = []

# 5 thread başlatma
for i in range(200):
    t = threading.Thread(target=click_target, args=(target_position,))
    t.start()
    threads.append(t)

# Tüm threadlerin tamamlanmasını bekle
for t in threads:
    t.join()

print("Program sonlandırıldı.")
