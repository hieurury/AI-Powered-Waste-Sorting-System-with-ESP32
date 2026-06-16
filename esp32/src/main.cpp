#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "camera_config.h"
#include "secrets.h"

// --- WIFI & SERVER CONFIGURATION ---
const char* ssid = SECRET_SSID;
const char* password = SECRET_PASS;
const char* serverName = SECRET_SERVER_URL; // Your server IP

// --- PIN DECLARATIONS ---
const int echo = 40;    // Connect to Echo pin of HC-SR04
const int trigger = 41; // Connect to Trig pin of HC-SR04
const int buzzer = 42;  // Connect to positive (+) pole of Buzzer
const int led_green = 39; // Connect to positive (+) pole of Green LED

bool isCaptured = false; 

float getDistance() {
    digitalWrite(trigger, LOW);
    delayMicroseconds(2);
    digitalWrite(trigger, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigger, LOW);
    
    long duration = pulseIn(echo, HIGH, 30000); 
    if (duration == 0) return 999.0; // Return 999.0 if error
    return duration * 0.034 / 2;
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    // Initialize hardware pins
    pinMode(trigger, OUTPUT);
    pinMode(echo, INPUT);
    pinMode(buzzer, OUTPUT);
    pinMode(led_green, OUTPUT);
    
    digitalWrite(buzzer, LOW); // Ensure buzzer is off initially
    digitalWrite(led_green, HIGH); // Turn ON LED to indicate system is READY

    // 1. CONNECT TO WIFI
    Serial.print("Connecting to WiFi");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi Connected!");
    Serial.print("ESP32 IP Address: ");
    Serial.println(WiFi.localIP());

    // 2. INIT CAMERA
    if (!initCamera()) {
        Serial.println("Camera initialization failed!");
        while (true) delay(1000);
    }
    
    Serial.println("System is READY. Waiting for objects...");
}

void loop() {
    float distance = getDistance();
    
    // ONLY PRINT DISTANCE TO SCREEN
    if (distance == 999.0) {
        Serial.println("Distance: ERROR");
    } else {
        Serial.print("Distance: ");
        Serial.print(distance);
        Serial.println(" cm");
    }

    // CHECK CONDITION 2 - 5 cm TO CAPTURE PHOTO
    if (distance >= 2.0 && distance <= 5.0) {
        if (!isCaptured) {

            // System is busy: Turn OFF the ready LED
            digitalWrite(led_green, LOW);

            delay(200); // Focus/Exposure delay for camera sensor

            // Beep the buzzer to notify user
            digitalWrite(buzzer, HIGH);
            delay(100);
            digitalWrite(buzzer, LOW);
            
            // Proceed to capture
            camera_fb_t *fb = capturePhoto();
            if (fb != nullptr) {
                Serial.println("Photo captured! Sending to server via Wi-Fi...");

                // HTTP POST
                if (WiFi.status() == WL_CONNECTED) {
                    HTTPClient http;
                    http.begin(serverName);
                    
                    // Declare payload data type as binary image
                    http.addHeader("Content-Type", "image/jpeg");

                    // Send the entire byte array of the image to the Server
                    int httpResponseCode = http.POST(fb->buf, fb->len);

                    if (httpResponseCode > 0) {
                        Serial.printf("Server Response Code: %d\n", httpResponseCode);
                    } else {
                        Serial.printf("Error occurred: %d\n", httpResponseCode);
                    }
                    http.end(); // Free resources
                } else {
                    Serial.println("Error: WiFi Disconnected");
                }

                releasePhoto(fb);
                isCaptured = true; 
                Serial.println("Processing done. Please remove the object.");
            } else {
                // If capture failed, turn the ready LED back on so it can retry
                digitalWrite(led_green, HIGH);
            }
        }
    }
    
    // CHECK RESET CONDITION WHEN HAND IS REMOVED (Distance > 15cm)
    if (distance > 15.0 && distance != 999.0 && isCaptured) {
        isCaptured = false; 
        digitalWrite(led_green, HIGH); // Turn ON LED to indicate system is READY again
        Serial.println("System is READY. Waiting for next object...");
    }

    delay(200); // 200ms delay to make loop responsive without hanging the sensor
}