from app import app
from extensions import db
from models import Course, CourseModule, LearningExperience, ISTEStandard, Material, LearningExperienceRequirement, Comment, Resource
from routes import seed_rubric_bank_items

def populate():
    with app.app_context():
        # 1. Limpieza total
        db.drop_all()
        db.create_all()
        print("Base de datos reiniciada con éxito.")

        # 2. Carga de Estándares ISTE
        iste_data = [
            ('1.1', 'Aprendiz Empoderado'),
            ('1.2', 'Ciudadano Digital'),
            ('1.3', 'Constructor de Conocimiento'),
            ('1.4', 'Diseñador Innovador'),
            ('1.5', 'Pensador Computacional'),
            ('1.6', 'Comunicador Creativo'),
            ('1.7', 'Colaborador Global')
        ]
        iste_objs = {}
        for code, desc in iste_data:
            obj = ISTEStandard(code=code, description=desc)
            db.session.add(obj)
            iste_objs[code] = obj
        db.session.commit()

        seed_rubric_bank_items()

        # 3. Carga de Materiales Base (Inventario)
        materials_list = [
            ('Arduino Uno', 10, 'pzs'),
            ('ESP32 NodeMCU', 8, 'pzs'),
            ('Servomotor SG90', 25, 'pzs'),
            ('Sensor Ultrasónico HC-SR04', 15, 'pzs'),
            ('Sensor de Humedad de Suelo', 10, 'pzs'),
            ('Módulo Relé 5V', 5, 'pzs'),
            ('Batería LiPo 3.7V', 10, 'pzs'),
            ('LED RGB', 50, 'pzs'),
            ('Resistencia 330 ohm', 100, 'pzs'),
            ('Cables Jumper M-M', 200, 'pzs')
        ]
        mat_objs = {}
        for name, stock, unit in materials_list:
            obj = Material(name=name, stock=stock, unit=unit)
            db.session.add(obj)
            mat_objs[name] = obj
        db.session.commit()

        # 4. Proyectos Ejemplo

        # 4a. Curso y modulos para formacion docente
        course = Course(
            title='Tecnologia Educativa para Docentes Normalistas',
            description='Ruta base para pedagogos y normalistas que inician en programacion aplicada al aula.',
            target_profile='Docentes sin perfil tecnico especializado',
            duration='6 semanas',
        )
        db.session.add(course)
        db.session.flush()
        module_1 = CourseModule(course_id=course.id, title='Fundamentos de pensamiento computacional', sequence=1)
        module_2 = CourseModule(course_id=course.id, title='Prototipos didacticos de bajo costo', sequence=2)
        db.session.add(module_1)
        db.session.add(module_2)
        db.session.flush()

        db.session.add(
            Resource(
                title='Guia visual: Secuencias y ciclos para docentes',
                resource_type='infographic',
                description='Infografia de apoyo para explicar secuencias, condicionales y ciclos en clase.',
                url='https://example.com/infografia-secuencias',
                course_id=course.id,
                module_id=module_1.id,
            )
        )
        db.session.add(
            Resource(
                title='Video corto: Como facilitar una clase de programacion sin perfil tecnico',
                resource_type='video',
                description='Estrategias para normalistas y pedagogos en su primera implementacion.',
                url='https://example.com/video-facilitacion',
                course_id=course.id,
                module_id=module_1.id,
            )
        )

        # EXPERIENCIA 1: Brazo Robótico Simple
        p1 = LearningExperience(
            title='Brazo Robótico Programable',
            level='Secundaria',
            module_id=module_2.id,
            workflow_status='published',
            board_stage='lista',
            week_slot=1,
            is_template=True,
            teacher_profile='Docente normalista con nociones basicas de computacion',
            course_focus='Pensamiento computacional aplicado a proyectos guiados',
            learning_objective='Ayudar al docente a traducir conceptos de secuencias, ciclos y precision en una experiencia tangible y explicable para adolescentes.',
            classroom_application='Puede implementarse como demostracion guiada o como reto por equipos en una clase de tecnologia o ciencias.',
            minimal_technology='Una computadora por equipo y un Arduino Uno compartido',
            estimated_duration='90 minutos',
            planning_markdown="""# Reto: Mecánica y Programación
## Inicio
Analizar cómo los robots industriales ayudan en tareas repetitivas o peligrosas.
## Desarrollo
1. Ensamblar la estructura del brazo usando piezas de madera o impresión 3D.
2. Conectar 3 servomotores al Arduino Uno.
3. Programar una secuencia de movimientos para mover un objeto de un punto A a un punto B.
## Cierre
Discutir los límites de precisión de los servos económicos y cómo mejorar la estabilidad.""",
            image_file='default.jpg'
        )
        p1.iste_standards.append(iste_objs['1.4'])
        p1.iste_standards.append(iste_objs['1.5'])
        db.session.add(p1)
        db.session.flush()
        db.session.add(LearningExperienceRequirement(learning_experience_id=p1.id, material_id=mat_objs['Arduino Uno'].id, quantity_needed=1))
        db.session.add(LearningExperienceRequirement(learning_experience_id=p1.id, material_id=mat_objs['Servomotor SG90'].id, quantity_needed=3))

        # EXPERIENCIA 2: Huerto Inteligente IoT
        p2 = LearningExperience(
            title='Sistema de Riego Automático IoT',
            level='Preparatoria',
            module_id=module_2.id,
            workflow_status='review',
            board_stage='en_clase',
            week_slot=1,
            is_template=False,
            teacher_profile='Docente de ciencias o tecnologia con interes en proyectos interdisciplinarios',
            course_focus='Integracion de programacion, datos y sostenibilidad',
            learning_objective='Mostrar al docente como conectar programacion basica y analisis de datos con problemas reales del entorno escolar.',
            classroom_application='Funciona como proyecto de cierre para materias STEAM o para clubes escolares con enfoque ambiental.',
            minimal_technology='Una computadora con Wi-Fi y un ESP32 por equipo',
            estimated_duration='2 sesiones de 50 minutos',
            planning_markdown="""# Proyecto: Sustentabilidad y Datos
## Inicio
Investigar el desperdicio de agua en la agricultura y cómo la tecnología puede optimizar el riego.
## Desarrollo
1. Configurar el ESP32 para conectarse a la red local.
2. Calibrar el sensor de humedad de suelo en seco y en mojado.
3. Programar un umbral para activar el relé que controla una pequeña bomba de agua.
## Cierre
Analizar los datos de humedad obtenidos y proponer mejoras en el algoritmo de riego.""",
            image_file='default.jpg'
        )
        p2.iste_standards.extend([iste_objs['1.3'], iste_objs['1.5'], iste_objs['1.7']])
        db.session.add(p2)
        db.session.flush()
        db.session.add(LearningExperienceRequirement(learning_experience_id=p2.id, material_id=mat_objs['ESP32 NodeMCU'].id, quantity_needed=1))
        db.session.add(LearningExperienceRequirement(learning_experience_id=p2.id, material_id=mat_objs['Sensor de Humedad de Suelo'].id, quantity_needed=1))
        db.session.add(LearningExperienceRequirement(learning_experience_id=p2.id, material_id=mat_objs['Módulo Relé 5V'].id, quantity_needed=1))

        # --- 4b. Curso: Programación Creativa con Artes ---
        course2 = Course(
            title='Programación Creativa: Arte y Expresión Digital',
            description='Explora la intersección entre las artes visuales, la música y la programación a través de proyectos creativos.',
            target_profile='Docentes de arte, música o humanidades interesados en integrar tecnología',
            duration='4 semanas',
        )
        db.session.add(course2)
        db.session.flush()
        mod2_1 = CourseModule(course_id=course2.id, title='Scratch y animación narrativa', sequence=1)
        mod2_2 = CourseModule(course_id=course2.id, title='Arduino y arte interactivo', sequence=2)
        db.session.add_all([mod2_1, mod2_2])
        db.session.flush()

        db.session.add(Resource(
            title='Galería de proyectos Scratch para primaria',
            resource_type='link',
            description='Colección curada de animaciones y juegos hechos con Scratch por docentes.',
            url='https://scratch.mit.edu/explore/projects/all',
            course_id=course2.id,
            module_id=mod2_1.id,
        ))
        db.session.add(Resource(
            title='Tutorial: LEDs y música con Arduino',
            resource_type='video',
            description='Cómo sincronizar luces LED al ritmo de una canción usando un sensor de sonido.',
            url='https://example.com/video-arduino-musica',
            course_id=course2.id,
            module_id=mod2_2.id,
        ))

        # EXPERIENCIA 3: Historia Animada con Scratch
        p3 = LearningExperience(
            title='Historia Animada con Scratch',
            level='Primaria',
            module_id=mod2_1.id,
            workflow_status='draft',
            board_stage='por_planear',
            week_slot=2,
            is_template=True,
            teacher_profile='Docente de español o artes sin experiencia en programación',
            course_focus='Narrativa digital y pensamiento computacional',
            learning_objective='Que el docente pueda guiar a sus alumnos para contar una historia corta usando animaciones, diálogos y fondos en Scratch.',
            classroom_application='Ideal para proyectos de comprensión lectora o escritura creativa en primaria superior.',
            minimal_technology='Computadora con acceso a scratch.mit.edu (sin instalación)',
            estimated_duration='60 minutos',
            planning_markdown="""# Historia Animada en Scratch
## Apertura
Leer en voz alta un cuento corto y preguntar: ¿qué personajes tendría tu historia?

## Desarrollo
1. Crear una cuenta en Scratch y explorar la interfaz: escenario, personajes y bloques.
2. Elegir o dibujar al menos 2 personajes y un fondo.
3. Programar diálogos usando bloques **decir** y **esperar**.
4. Agregar animación con bloques de movimiento y disfraces.

## Cierre
Compartir el proyecto con el código URL y dar retroalimentación entre equipos.""",
            image_file='default.jpg'
        )
        p3.iste_standards.extend([iste_objs['1.4'], iste_objs['1.6']])
        db.session.add(p3)

        # EXPERIENCIA 4: Galería de Arte Interactivo con LEDs
        p4 = LearningExperience(
            title='Galería de Arte Interactivo con LEDs',
            level='Secundaria',
            module_id=mod2_2.id,
            workflow_status='draft',
            board_stage='por_planear',
            week_slot=2,
            is_template=False,
            teacher_profile='Docente de artes visuales con curiosidad tecnológica',
            course_focus='Integración de electrónica y expresión artística',
            learning_objective='Crear una instalación artística donde los alumnos controlen patrones de luz mediante código, fusionando diseño visual y programación.',
            classroom_application='Proyecto de cierre para una unidad de arte contemporáneo o como participación en feria de talentos.',
            minimal_technology='Arduino Uno y tira de LEDs RGB por equipo',
            estimated_duration='2 sesiones de 50 minutos',
            planning_markdown="""# Instalación de Arte y Luz
## Apertura
Ver ejemplos de arte con luz: James Turrell, TeamLab. ¿Cómo el código puede ser un pincel?

## Desarrollo
1. Conectar una tira de 5 LEDs RGB al Arduino.
2. Programar 3 patrones de color: estático, parpadeante y arcoíris.
3. Diseñar una "obra" eligiendo paleta y ritmo, justificando la elección artística.

## Cierre
Montar una mini galería en el aula y que cada equipo explique el concepto detrás de su instalación.""",
            image_file='default.jpg'
        )
        p4.iste_standards.extend([iste_objs['1.4'], iste_objs['1.6'], iste_objs['1.2']])
        db.session.add(p4)
        db.session.flush()
        db.session.add(LearningExperienceRequirement(learning_experience_id=p4.id, material_id=mat_objs['Arduino Uno'].id, quantity_needed=1))
        db.session.add(LearningExperienceRequirement(learning_experience_id=p4.id, material_id=mat_objs['LED RGB'].id, quantity_needed=5))
        db.session.add(LearningExperienceRequirement(learning_experience_id=p4.id, material_id=mat_objs['Resistencia 330 ohm'].id, quantity_needed=5))
        db.session.add(LearningExperienceRequirement(learning_experience_id=p4.id, material_id=mat_objs['Cables Jumper M-M'].id, quantity_needed=10))

        # --- 4c. Curso: Robótica en Educación Especial ---
        course3 = Course(
            title='Robótica Accesible e Inclusiva',
            description='Estrategias y experiencias para introducir la robótica y la programación en contextos de educación especial y atención a la diversidad.',
            target_profile='Docentes de educación especial, USAER y apoyo psicopedagógico',
            duration='5 semanas',
        )
        db.session.add(course3)
        db.session.flush()
        mod3_1 = CourseModule(course_id=course3.id, title='Robótica desenchufada y adaptada', sequence=1)
        mod3_2 = CourseModule(course_id=course3.id, title='Interfaces sencillas con micro:bit', sequence=2)
        mod3_3 = CourseModule(course_id=course3.id, title='Proyectos de autonomía personal', sequence=3)
        db.session.add_all([mod3_1, mod3_2, mod3_3])
        db.session.flush()

        db.session.add(Resource(
            title='Guía de actividades desenchufadas para educación especial',
            resource_type='document',
            description='Actividades de algoritmos y secuencias sin necesidad de computadora.',
            url='https://example.com/guia-desenchufada',
            course_id=course3.id,
            module_id=mod3_1.id,
        ))

        # EXPERIENCIA 5: El Robot de Papel
        p5 = LearningExperience(
            title='El Robot de Papel: Algoritmos sin Pantalla',
            level='Primaria',
            module_id=mod3_1.id,
            workflow_status='published',
            board_stage='archivada',
            week_slot=3,
            is_template=True,
            teacher_profile='Docente de educación especial o apoyo USAER',
            course_focus='Pensamiento computacional desenchufado y comunicación aumentativa',
            learning_objective='Desarrollar la noción de secuencia e instrucción precisa usando tarjetas de movimiento físicas, adaptable a diferentes niveles de autonomía.',
            classroom_application='Funciona como introducción al pensamiento computacional sin barreras tecnológicas. Puede adaptarse a BAC (Comunicación Aumentativa).',
            minimal_technology='Sin tecnología digital requerida. Solo tarjetas impresas.',
            estimated_duration='45 minutos',
            planning_markdown="""# Robot de Papel
## Apertura
Jugar a "Simón dice" con instrucciones muy precisas: avanza 2 pasos, gira a la derecha.

## Desarrollo
1. Repartir tarjetas de movimiento: ↑ Avanzar, ↻ Girar derecha, ↺ Girar izquierda, ⬛ Detenerse.
2. Un alumno es el "robot" y sigue las tarjetas en orden.
3. En parejas, diseñar una secuencia para llevar al robot de la silla al pizarrón.
4. Opcional: contar las instrucciones y reflexionar si se puede hacer con menos.

## Cierre
¿Qué pasó cuando faltó una instrucción? ¿Qué es un bug?""",
            image_file='default.jpg'
        )
        p5.iste_standards.extend([iste_objs['1.5'], iste_objs['1.1']])
        db.session.add(p5)

        # EXPERIENCIA 6: Semáforo con micro:bit
        p6 = LearningExperience(
            title='Mi Primer Semáforo con micro:bit',
            level='Secundaria',
            module_id=mod3_2.id,
            workflow_status='review',
            board_stage='ajustar',
            week_slot=3,
            is_template=False,
            teacher_profile='Docente de apoyo técnico o director de taller de tecnología inclusiva',
            course_focus='Autonomía, señalización y programación visual por bloques',
            learning_objective='Construir un semáforo funcional usando MakeCode por bloques, trabajando secuencias condicionales en un contexto de vida cotidiana relevante.',
            classroom_application='Proyecto motivador para alumnos con discapacidad intelectual leve o moderada. El contexto del semáforo es familiar y significativo.',
            minimal_technology='micro:bit v2 y cable USB por equipo, MakeCode en navegador',
            estimated_duration='60 minutos',
            planning_markdown="""# Semáforo Digital
## Apertura
Mostrar imágenes de semáforos. ¿Para qué sirven? ¿Qué pasa si fallan?

## Desarrollo
1. Abrir MakeCode (makecode.microbit.org) y explorar los bloques de LEDs.
2. Programar una secuencia: rojo 3s → amarillo 1s → verde 3s en bucle.
3. Agregar sonido: pitido corto al cambiar a verde.
4. Descargar el programa al micro:bit y probarlo.

## Cierre
¿Podrías agregar un botón para que el peatón solicite el cambio de luz? Diseñarlo en papel.""",
            image_file='default.jpg'
        )
        p6.iste_standards.extend([iste_objs['1.4'], iste_objs['1.5']])
        db.session.add(p6)

        # EXPERIENCIA 7: Asistente de Rutinas
        p7 = LearningExperience(
            title='Asistente de Rutinas con Sensor de Movimiento',
            level='Preparatoria',
            module_id=mod3_3.id,
            workflow_status='draft',
            board_stage='por_planear',
            week_slot=4,
            is_template=False,
            teacher_profile='Docente especialista en tecnología de apoyo o terapia ocupacional',
            course_focus='Tecnología asistiva y autonomía personal',
            learning_objective='Diseñar un dispositivo que detecte movimiento y emita una alerta visual/sonora como apoyo a la rutina diaria de alumnos con necesidades de autonomía.',
            classroom_application='Aplicable en talleres de vida independiente o transición a la vida adulta. Muy motivador para familias.',
            minimal_technology='Arduino Uno, sensor ultrasónico y buzzer por equipo',
            estimated_duration='2 sesiones de 60 minutos',
            planning_markdown="""# Asistente de Rutinas
## Apertura
¿Qué dispositivos usamos para recordar cosas? Alarmas, timers, luces. ¿Cómo se programan?

## Desarrollo
### Sesión 1
1. Conectar el sensor HC-SR04 al Arduino.
2. Leer distancias en el monitor serial y calibrar el rango de detección (ej. 0-30 cm).

### Sesión 2
3. Agregar un buzzer y programar: si distancia < 30cm → sonar 2 veces.
4. Personalizar: ¿Para qué momento de la rutina sería útil este dispositivo?

## Cierre
Presentar el proyecto explicando qué problema de autonomía resuelve y para quién.""",
            image_file='default.jpg'
        )
        p7.iste_standards.extend([iste_objs['1.4'], iste_objs['1.3'], iste_objs['1.1']])
        db.session.add(p7)
        db.session.flush()
        db.session.add(LearningExperienceRequirement(learning_experience_id=p7.id, material_id=mat_objs['Arduino Uno'].id, quantity_needed=1))
        db.session.add(LearningExperienceRequirement(learning_experience_id=p7.id, material_id=mat_objs['Sensor Ultrasónico HC-SR04'].id, quantity_needed=1))
        db.session.add(LearningExperienceRequirement(learning_experience_id=p7.id, material_id=mat_objs['Cables Jumper M-M'].id, quantity_needed=8))

        # --- 4d. Curso: Ciencia de Datos para Bachillerato ---
        course4 = Course(
            title='Introducción a Ciencia de Datos en el Aula',
            description='Ruta para que docentes de matemáticas y ciencias integren análisis de datos reales en sus clases usando herramientas accesibles.',
            target_profile='Docentes de matemáticas, física o biología a nivel bachillerato',
            duration='6 semanas',
        )
        db.session.add(course4)
        db.session.flush()
        mod4_1 = CourseModule(course_id=course4.id, title='Recolección y limpieza de datos', sequence=1)
        mod4_2 = CourseModule(course_id=course4.id, title='Visualización con hojas de cálculo', sequence=2)
        mod4_3 = CourseModule(course_id=course4.id, title='Python básico para análisis', sequence=3)
        db.session.add_all([mod4_1, mod4_2, mod4_3])
        db.session.flush()

        db.session.add(Resource(
            title='Dataset abierto: calidad del aire en ciudades mexicanas',
            resource_type='link',
            description='Portal del gobierno con datos de contaminantes descargables en CSV.',
            url='https://datos.gob.mx/busca/dataset/calidad-del-aire',
            course_id=course4.id,
            module_id=mod4_1.id,
        ))
        db.session.add(Resource(
            title='Google Colab: entorno Python gratuito en el navegador',
            resource_type='link',
            description='Sin instalación, ideal para el aula. Incluye pandas y matplotlib preinstalados.',
            url='https://colab.research.google.com',
            course_id=course4.id,
            module_id=mod4_3.id,
        ))

        # EXPERIENCIA 8: Encuesta de Hábitos y Gráficas
        p8 = LearningExperience(
            title='Encuesta de Hábitos Escolares y Visualización',
            level='Preparatoria',
            module_id=mod4_2.id,
            workflow_status='published',
            board_stage='lista',
            week_slot=4,
            is_template=True,
            teacher_profile='Docente de matemáticas o estadística con manejo básico de Excel/Sheets',
            course_focus='Estadística aplicada y cultura de datos',
            learning_objective='Que los alumnos diseñen, apliquen y analicen una encuesta real, creando visualizaciones que apoyen la toma de decisiones escolares.',
            classroom_application='Proyecto transversal ideal para materias de estadística, formación cívica o tutoría. Los datos son de la propia comunidad escolar.',
            minimal_technology='Google Forms y Google Sheets (acceso a internet necesario)',
            estimated_duration='3 sesiones de 50 minutos',
            planning_markdown="""# Encuesta + Datos = Decisiones
## Sesión 1: Diseño
1. Definir la pregunta de investigación: ej. "¿Cuántas horas duermen los alumnos de bachillerato?"
2. Diseñar el formulario en Google Forms con al menos 5 preguntas (cerradas y abiertas).
3. Compartir el enlace y recolectar 30+ respuestas entre compañeros.

## Sesión 2: Limpieza
1. Exportar las respuestas a Google Sheets.
2. Identificar respuestas atípicas o faltantes y decidir qué hacer con ellas.
3. Calcular media, mediana y moda para las preguntas numéricas.

## Sesión 3: Visualización
1. Crear un gráfico de barras, uno circular y un histograma.
2. Redactar 3 conclusiones basadas en los datos.
3. Presentar los hallazgos al grupo con una diapositiva por conclusión.

## Cierre
¿Qué cambiarías en la escuela basándote en los datos? ¿Por qué los datos importan?""",
            image_file='default.jpg'
        )
        p8.iste_standards.extend([iste_objs['1.3'], iste_objs['1.5'], iste_objs['1.6']])
        db.session.add(p8)

        # EXPERIENCIA 9: Python para Analizar Datos del Sensor
        p9 = LearningExperience(
            title='Análisis de Temperatura con Python y pandas',
            level='Preparatoria',
            module_id=mod4_3.id,
            workflow_status='review',
            board_stage='en_clase',
            week_slot=4,
            is_template=False,
            teacher_profile='Docente con interés en programación básica, familiarizado con hojas de cálculo',
            course_focus='Ciencia de datos con Python accesible',
            learning_objective='Introducir pandas y matplotlib a través de un dataset de temperatura local, conectando la programación con el análisis científico real.',
            classroom_application='Proyecto de ciencia o matemáticas que puede escalar a un proyecto de feria científica.',
            minimal_technology='Google Colab (solo navegador con internet)',
            estimated_duration='2 sesiones de 60 minutos',
            planning_markdown="""# Python para Datos de Temperatura
## Apertura
Abrir Colab y ejecutar `print("Hola, datos!")`. Desmitificar la programación.

## Sesión 1: Cargar y Explorar
```python
import pandas as pd
df = pd.read_csv('temperaturas.csv')
print(df.head())
print(df.describe())
```
1. Interpretar las estadísticas descriptivas: ¿qué mes fue más caliente?

## Sesión 2: Visualizar
```python
import matplotlib.pyplot as plt
df.plot(x='fecha', y='temperatura', kind='line')
plt.title('Temperatura mensual')
plt.show()
```
2. Personalizar: cambiar colores, agregar una línea de promedio.
3. Exportar la gráfica como imagen para incluir en un reporte.

## Cierre
¿Qué preguntas nuevas generan tus gráficas? El análisis es un ciclo, no un final.""",
            image_file='default.jpg'
        )
        p9.iste_standards.extend([iste_objs['1.5'], iste_objs['1.3']])
        db.session.add(p9)

        # 5. Comentarios de prueba
        db.session.add(Comment(content="Excelente para trabajar lógica de ciclos con los de segundo año.", author="Profe Roel", learning_experience_id=p1.id))
        db.session.add(Comment(content="Cuidado con la corriente del ESP32, es mejor alimentar los sensores por separado.", author="Asesor Técnico", learning_experience_id=p2.id))
        db.session.add(Comment(content="Mis alumnos de 4° adoraron elegir sus propios personajes. Muy motivador.", author="Mtra. Fernanda", learning_experience_id=p3.id))
        db.session.add(Comment(content="El juego del robot de papel funcionó perfecto como primer día de clase.", author="Equipo USAER Zona 12", learning_experience_id=p5.id))
        db.session.add(Comment(content="Los datos de la encuesta sorprendieron a los alumnos. Nadie esperaba que el 60% durmiera menos de 6 horas.", author="Profe Martínez", learning_experience_id=p8.id))

        db.session.commit()
        print("Poblacion completada: 4 cursos, 9 experiencias, materiales y estandares ISTE.")

if __name__ == '__main__':
    populate()