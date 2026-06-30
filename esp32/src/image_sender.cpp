#include <Arduino.h>
#include "image_sender.h"

bool sendImageSerial(camera_fb_t *fb) {
    if (fb == nullptr) return false;

    // start
    Serial.println("START");
    Serial.println(fb->len);
    
    // send image data
    Serial.write(fb->buf, fb->len);
    
    // end
    Serial.println(); // newline character ensures END is on a new line
    Serial.println("END");

    return true;
}