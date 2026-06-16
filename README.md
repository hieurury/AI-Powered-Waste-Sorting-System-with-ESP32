# Smart IoT Waste Classification System

This repository is structured as a monorepo containing two main components:

* `/esp32`: The C++ firmware for the ESP32-S3 Camera microcontroller (developed using PlatformIO).
* `/server`: The Python backend containing the Flask web server, AI training script, and database integration.

## Prerequisites

Before running the project, make sure the following software is installed on your system:

* Python 3.8 or higher
* MongoDB Community Server (running on the default port 27017)
* Visual Studio Code with the PlatformIO extension (for uploading ESP32 firmware)
* Git

# Step 1: Clone the Repository

```bash
git clone https://github.com/hieurury/AI-Powered-Waste-Sorting-System-with-ESP32.git
```

# Step 2: Server Setup and Virtual Environment

Navigate to the `server` directory and begin the initial setup.

```bash
cd server

python setup.py
```

This command will automatically install the required dependencies and create the necessary folders and supporting files.

Activate the virtual environment:

**Windows**

Run the following command inside the `/server` directory:

```bash
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Continue with the deployment process:

```bash
python train.py
```

This command will start training the model using the provided dataset.

Once the training process is complete, a file named `model.h5` will be generated in the same directory as `server.py`.

Next, open the `.env` file and update the Database URI and other environment variables according to your personal configuration.

> At this point, the server setup is nearly complete.

# Step 3: ESP32 Hardware Setup

Open the `/esp32` directory using PlatformIO IDE or the PlatformIO extension in Visual Studio Code.

Navigate to the `include` folder and create a file named `secrets.h`.

Add the following content to `secrets.h`:

```cpp
#ifndef SECRETS_H
#define SECRETS_H

// Replace with your actual Wi-Fi credentials and Server IP
#define SECRET_SSID "Your_WiFi_Name"
#define SECRET_PASS "Your_WiFi_Password"
#define SECRET_SERVER_URL "http://192.168.X.X:5000/upload"

#endif
```

> Replace `X.X` with the IPv4 address of the machine running the server.

# Step 4: Upload the Firmware and Run the System

After configuring the environment variables and network settings, upload the firmware to your ESP32 board.

Make sure the hardware is wired according to the diagram below.

![[public/board.jpg]]

> After the upload is complete, the green LED should turn on. When an object or hand is placed near the sensor, the buzzer should sound.

On the server side, navigate to the `/server` directory and run:

```bash
python server.py
```

You should now see the server listening for incoming data from the ESP32 device.

Test the system by placing your hand near the sensor and verify whether the device captures an image and uploads it to the server.

If the server downloads the image and returns a classification result, or if a new image appears inside the `images` directory, the system is working correctly.

# Step 5: Database Customization

The application stores collected data in either a local database or your own database server.

Using the stored data, you can further develop and customize a client dashboard application for easier data management, monitoring, and statistical analysis.

The database can be extended to support additional features such as:

* Real-time monitoring of waste classification results
* Historical data tracking and reporting
* Waste collection statistics and analytics
* Device status monitoring
* Location-based waste management insights
* Exporting reports for further analysis

By building a dedicated dashboard, administrators can efficiently manage the system and gain valuable insights from the collected data.

---

# Important Notes

1. Ensure that the server IP address configured on the ESP32 is correct.
2. Make sure the device allows location access for third-party applications if location data collection is required.
3. Verify that the configuration in `platformio.ini` matches your hardware specifications. The current configuration is designed for the ESP32-S3 N16R8 variant.
