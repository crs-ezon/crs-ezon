import os
import csv
import cv2
import numpy as np
import time
from pymongo import MongoClient
import zwoasi as asi

# Initialize ZWO ASI SDK
SDK_PATH = r"asi2\x64\ASICamera2.dll"
asi.init(SDK_PATH)


# Functions for finding the brightest point and angle calculations
def find_brightest_point(frame):
    # Ensure frame is in grayscale for processing
    if len(frame.shape) == 3:  # Convert BGR to grayscale if necessary
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame

    _, binary = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
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
    return frame

def save_to_csv(data, csv_file):
    try:
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)
    except Exception as e:
        print(f'CSV writing error: {e}')

def save_to_db(data):
    try:
        client = MongoClient("mongodb+srv://crs:crskciri@cluster0.r7dz0yu.mongodb.net/")
        db = client["CRS"]
        collection = db["Angles"]

        # Print the data for debugging
        print(f"Inserting data: {data}")
        
        # Insert the data into MongoDB
        result = collection.insert_one(data)
        print(f"Data inserted with ID: {result.inserted_id}")
    except Exception as e:
        print(f"Error inserting data into MongoDB: {e}")

def save_image(frame, dir, timestamp):
    image_name = f'{timestamp}.jpg'
    image_path = os.path.join(dir, image_name)
    cv2.imwrite(image_path, frame)

def main():
    date = time.strftime('%Y-%m-%d', time.localtime())
    print(date)
    dest_folder = f'Angles_{date}'
    os.makedirs(dest_folder, exist_ok=True)
    csv_file = os.path.join(dest_folder, f'angles_{date}.csv')

    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'N-S', 'E-W'])

    # Initialize ZWO ASI camera
    num_cameras = asi.get_num_cameras()
    if num_cameras == 0:
        print("No ASI cameras found. Please connect a camera and try again.")
        return

    camera = asi.Camera(0)
    camera_info = camera.get_camera_property()
    print(f"Connected to camera: {camera_info['Name']}")

    camera.set_control_value(asi.ASI_GAIN, 100)
    camera.set_control_value(asi.ASI_EXPOSURE, 10000)
    camera.set_control_value(asi.ASI_BRIGHTNESS, 50)
    camera.set_control_value(asi.ASI_GAMMA, 50)

    camera.start_video_capture()

    try:
        last_save_time = time.time()
        save_interval = 1  # Capture and save every second
        while True:
            frame = camera.capture_video_frame()
            frame = np.frombuffer(frame, dtype=np.uint8).reshape(camera_info['MaxHeight'], camera_info['MaxWidth'])

            # Convert single-channel to BGR for processing
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            timestamp = time.strftime('%Y-%m-%d_%H%M%S', time.localtime())
            projections = {
                "Equirectangular": calculate_angles_equirectangular
            }

            angles_data = [timestamp]
            for name, func in projections.items():
                os.makedirs(os.path.join(dest_folder, name), exist_ok=True)
                os.chmod(os.path.join(dest_folder, name), 0o777)
                processed_frame = process_and_show_frame(frame.copy(), func, name)

                if time.time() - last_save_time >= save_interval:
                    save_image(processed_frame, os.path.join(dest_folder, name), timestamp)
                    centroid_x, centroid_y = find_brightest_point(frame)
                    if centroid_x is not None and centroid_y is not None:
                        angle_ns, angle_ew = func(centroid_x, centroid_y, frame.shape[1] // 2, frame.shape[0] // 2)
                        angles_data += [angle_ns, angle_ew]
                    else:
                        angles_data += [None, None]

            if len(angles_data) > 1:
                save_to_csv(angles_data, csv_file)
                try:
                    data = {"Time": str(angles_data[0]), "North-South": str(angles_data[1]), "East-West": str(angles_data[2])}
                    save_to_db(data)
                except:
                    data = {"Time": angles_data[0], "North-South": "N/A", "East-West": "N/A"}
                    save_to_db(data)
                last_save_time = time.time()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        camera.stop_video_capture()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
