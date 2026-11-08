#pragma once

namespace firmware::hal {

enum class Led { Green, Red };

void led_init();
void led_toggle(Led led);

}
