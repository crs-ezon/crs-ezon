import os
import csv
import cv2
import numpy as np
import time
#import RPi.GPIO as GPIO

# Setup GPIO
'''GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
LED_PIN = 18  # You can choose any available GPIO pin
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN, GPIO.HIGH)  # Turn on the LED to indicate program is running
'''
def find_brightest_point(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        max_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(max_contour)
        centroid_x = int(M["m10"] / (M["m00"] + 1e-5))
        centroid_y = int(M["m01"] / (M["m00"] + 1e-5))

        return centroid_x, centroid_y
    return None, None

def calculate_angles_stereographic(centroid_x, centroid_y, center_x, center_y):
    delta_x = centroid_x - center_x
    delta_y = center_y - centroid_y

    r = np.sqrt(delta_x**2 + delta_y**2)
    max_r = np.sqrt(center_x**2 + center_y**2)
    theta = np.arctan(r / max_r)

    angle_x = np.degrees(theta * delta_x / r) if r != 0 else 0
    angle_y = np.degrees(theta * delta_y / r) if r != 0 else 0

    return -1*angle_x, -1*angle_y

def calculate_angles_equidistant(centroid_x, centroid_y, center_x, center_y):
    delta_x = centroid_x - center_x
    delta_y = center_y - centroid_y

    radius = np.sqrt(delta_x**2 + delta_y**2)
    max_radius = np.sqrt(center_x**2 + center_y**2)

    angle_x = (delta_x / max_radius) * 90
    angle_y = (delta_y / max_radius) * 90

    return -1*angle_x, -1*angle_y

def calculate_angles_equirectangular(centroid_x, centroid_y, center_x, center_y):
    delta_x = centroid_x - center_x
    delta_y = center_y - centroid_y

    angle_x = (delta_x / center_x) * 90
    angle_y = (delta_y / center_y) * 90

    return -1*angle_x, -1*angle_y

def draw_axes(frame):
    height, width = frame.shape[:2]
    center_x = width // 2
    center_y = height // 2

    cv2.line(frame, (0, center_y), (width, center_y), (0, 255, 0), 2)
    cv2.line(frame, (center_x, 0), (center_x, height), (0, 255, 0), 2)

def process_and_show_frame(frame, projection_func, window_name):
    center_x = frame.shape[1] // 2
    center_y = frame.shape[0] // 2

    centroid_x, centroid_y = find_brightest_point(frame)

    if centroid_x is not None:
        angle_x, angle_y = projection_func(centroid_x, centroid_y, center_x, center_y)
        cv2.circle(frame, (centroid_x, centroid_y), 5, (0, 0, 255), -1)
        cv2.putText(frame, f"E-W: {angle_x:.2f}°, N-S: {angle_y:.2f}°", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    draw_axes(frame)
    cv2.putText(frame, window_name, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.imshow(window_name, frame)
    return frame
def save_to_csv(data, csv_file):
    try:
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)
    except Exception as e:
        print(f'CSV writing error: {e}')

def save_image(frame, dir, timestamp):
    image_name = f'frame_{timestamp}.jpg'
    image_path = os.path.join(dir, image_name)
    cv2.imwrite(image_path, frame)

def main():
    date=time.strftime('%Y-%m-%d',time.localtime())
    print(date)
    dest_folder = f'Angles_{date}'
    os.makedirs(dest_folder, exist_ok=True)
    csv_file = os.path.join(dest_folder, f'angles_{date}.csv')
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Stereographic_NS', 'Stereographic_EW',
                             'Equidistant_NS', 'Equidistant_EW',
                             'Equirectangular_NS', 'Equirectangular_EW'])
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Camera not accessible")
        #GPIO.output(LED_PIN, GPIO.LOW)  # Turn off the LED
        return
    try:
        last_save_time=time.time()
        save_interval=30
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture image")
                break
            timestamp = time.strftime('%Y-%m-%d_%H%M%S', time.localtime())
            projections = {
                "Stereographic": calculate_angles_stereographic,
                "Equidistant": calculate_angles_equidistant,
                "Equirectangular": calculate_angles_equirectangular
            }
            angles_data=[timestamp]
            for name, func in projections.items():
                os.makedirs(os.path.join(dest_folder, name), exist_ok=True)
                processed_frame=process_and_show_frame(frame.copy(), func, name)
                if time.time() - last_save_time >= save_interval:
                    save_image(processed_frame, os.path.join(dest_folder, name), timestamp)
                    angle_ns, angle_ew = func(*find_brightest_point(frame), frame.shape[1] // 2, frame.shape[0] // 2)
                    angles_data += [angle_ns, angle_ew]
            if len(angles_data)>1:
                save_to_csv(angles_data,csv_file)
                last_save_time=time.time()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        #GPIO.output(LED_PIN, GPIO.LOW)  # Turn off the LED
        #GPIO.cleanup()  # Clean up GPIO settings

if __name__ == "__main__":
    main()