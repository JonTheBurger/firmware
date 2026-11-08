#include <main.h>
#include "stm32f4xx_hal_gpio.h"

int main()
{
  stm32f429i_disc1_init();

  while (true)
  {
    HAL_GPIO_TogglePin(LD3_GPIO_Port, LD3_Pin);
    HAL_GPIO_TogglePin(LD4_GPIO_Port, LD4_Pin);
    HAL_Delay(500);
  }
  return 0;
}
