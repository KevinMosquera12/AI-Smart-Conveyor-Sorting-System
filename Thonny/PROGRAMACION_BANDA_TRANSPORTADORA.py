from machine import Pin, PWM, SPI, UART
import time
from ili9341 import Display, color565

# ========================
# Configuración de SPI y Pantalla ILI9341
# ========================
spi = SPI(1, baudrate=20000000, sck=Pin(18), mosi=Pin(23), miso=Pin(12))
display = Display(spi, dc=Pin(2), cs=Pin(15), rst=Pin(4), bgr=False)

def mostrar_estado_en_pantalla(texto, color):
    display.clear()
    x = (240 - len(texto) * 8) // 2
    display.draw_text8x8(x, 120, texto, color)

# ========================
# Pines del motor L298N
# ========================
IN1 = Pin(22, Pin.OUT)
IN2 = Pin(19, Pin.OUT)
ENA = PWM(Pin(5), freq=500)

VELOCIDAD_FIJA = 1023

def set_motor_speed(speed):
    ENA.duty(speed)

def motor_adelante():
    IN1.value(1)
    IN2.value(0)
    set_motor_speed(VELOCIDAD_FIJA)

def detener_motor():
    IN1.value(0)
    IN2.value(0)
    set_motor_speed(0)

# ========================
# Sensor ultrasónico HC-SR04
# ========================
class Ultrasonico:
    def __init__(self, trigger_pin, echo_pin):
        self.trigger = Pin(trigger_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)

    def distancia_cm(self):
        self.trigger.value(0)
        time.sleep_us(2)
        self.trigger.value(1)
        time.sleep_us(10)
        self.trigger.value(0)

        while self.echo.value() == 0:
            pass
        start = time.ticks_us()

        while self.echo.value() == 1:
            pass
        end = time.ticks_us()

        duration = time.ticks_diff(end, start)
        return duration * 0.0343 / 2  # cm

# Instancia de sensores
sensor_inicio = Ultrasonico(trigger_pin=13, echo_pin=34)
sensor_final = Ultrasonico(trigger_pin=27, echo_pin=14)

# ========================
# Configurar UART para recibir datos
# ========================
uart = UART(2, baudrate=9600, rx=16, tx=17)  # Ajusta los pines según tu conexión

def leer_color_uart():
    if uart.any():
        try:
            linea = uart.readline()
            if linea:
                color = linea.decode('utf-8').strip()
                print("Color recibido por UART:", color)  # Imprime en terminal
                return color
        except Exception as e:
            print("Error decodificando UART:", e)
    return None

# ========================
# Configuración del servo (ejemplo en pin 21)
# ========================
servo = PWM(Pin(21), freq=50)  # Frecuencia 50Hz para servos estándar

def angulo_a_duty(angulo):
    # Convierte ángulo 0-180 a duty entre 40 y 115 (ajusta si es necesario)
    # En ESP32 duty range PWM 0-1023, pero MicroPython usa duty 0-1023
    # Pulsos típicos para servo: 1ms (5% duty cycle) a 2ms (10% duty cycle)
    # Con 50Hz, periodo = 20ms, 5% = 1ms, 10% = 2ms
    # duty = porcentaje * 1023 / 100
    min_duty = 40  # aprox 2% (ajusta si es necesario)
    max_duty = 115  # aprox 5.6%
    duty = int(min_duty + (angulo / 180) * (max_duty - min_duty))
    return duty

def mover_servo(angulo):
    duty = angulo_a_duty(angulo)
    servo.duty(duty)
    print(f"Servo movido a {angulo}° (duty={duty})")
    
# ========================
# Programa principal
# ========================
try:
    print("?? Sistema de banda transportadora iniciado...")
    
    banda_activa_por_color = False  # Controla si banda está activada por color y no repetir

    while True:
        # Leer sensores ultrasónicos
        distancia_inicio = sensor_inicio.distancia_cm()
        distancia_final = sensor_final.distancia_cm()

        print(f"Inicio: {distancia_inicio:.1f} cm | Final: {distancia_final:.1f} cm")
        

        # Control motor según sensores ultrasónicos
        if distancia_inicio < 10:
            print("?? Caja detectada al inicio ? Iniciando banda")
            mostrar_estado_en_pantalla("Caja detectada", color565(0, 255, 0))
            motor_adelante()
            time.sleep(2.4)
            
            
             # Resetear el flag para permitir activar banda por color luego
            banda_activa_por_color = False

        if distancia_final < 10:
            print("? Caja llegó al final ? Deteniendo banda")
            mostrar_estado_en_pantalla("Caja al final", color565(255, 0, 0))
            detener_motor()
            time.sleep(2.4)
            mostrar_estado_en_pantalla("Esperando caja", color565(255, 255, 0))

        # Leer color enviado por UART
        color_recibido = leer_color_uart()
        if color_recibido:
            colores_map = {
                 'Rojo': (color565(255, 0, 0), 0),       # Ángulo 0°
                'Verde': (color565(0, 255, 0), 45),    # Ángulo 45°
                'Azul': (color565(0, 0, 255), 90),     # Ángulo 90°
                'Amarillo': (color565(255, 255, 0), 135) # Ángulo 135°
            }
            color_mostrar, angulo = colores_map.get(color_recibido, (color565(255, 255, 255), 0))
            mostrar_estado_en_pantalla(color_recibido, color_mostrar)
            mover_servo(angulo)
            
            
             # Activar banda por 5 segundos sólo si está detenida y no ha sido activada antes por el color actual
            if distancia_final < 10 and not banda_activa_por_color:
                print("🔄 Activando banda por 2 segundos tras detectar color")
                motor_adelante()
                time.sleep(2)
                detener_motor()
                print("🛑 Banda detenida")
                mostrar_estado_en_pantalla("Banda detenida", color565(255, 0, 0))
                time.sleep(1)
                mostrar_estado_en_pantalla("Esperando caja", color565(255, 255, 0))
                banda_activa_por_color = True

        time.sleep(0.2)

except Exception as e:
    print(f"? Error: {e}")
    detener_motor()

except KeyboardInterrupt:
    print("?? Ejecución detenida por usuario")
    detener_motor()
