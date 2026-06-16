#ifndef CAMERA_CONFIG_H
#define CAMERA_CONFIG_H

#include <Arduino.h>
#include "esp_camera.h"

bool initCamera();
camera_fb_t* capturePhoto();
void releasePhoto(camera_fb_t* fb);

#endif