#include <Arduino.h>
#include "image_sender.h"

bool sendImageSerial(camera_fb_t *fb) {
    if (fb == nullptr) return false;

    // Bắt đầu truyền
    Serial.println("START");
    Serial.println(fb->len);
    
    // Truyền dữ liệu nhị phân
    Serial.write(fb->buf, fb->len);
    
    // Kết thúc truyền
    Serial.println(); // Ký tự ngắt dòng đảm bảo END nằm ở dòng mới
    Serial.println("END");

    return true;
}