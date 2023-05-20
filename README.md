# Проект
**План**
- Описание темы
- Описание машинного обучения и гипотез


**Команда**
- Коломоец Эвелина
- Нагорская Мария
- Сомонов Данил 

## Тема
Данные берем с 2008 по 2023 год. 
Мы собираемся спарсить ключевую ставку ЦБ РФ и ФРС (индикаторы монетарной политики). Также цену золота (динамика цен защитного актива) с сайта ЦБ, значение индекса IMOEX с сайта Московской биржи (индикатор состояния ключевых компаний российского рынка; кроме того, по нему можно отслеживать негативный новостной фон). Дополняем датасет инфляцией РФ и США. Все эти показатели либо отражают макроэкономическую ситуацию и состояние финансового рынка в РФ, либо представляют собой те признаки, которые могут на это повлиять.

Категориальными (новыми) признаками будут мягкая или жесткая денежная кредитная политика в РФ и в США (смотрится по ставке и инфляции), а также рабочий/нерабочий день (парсим производственный календарь). 

Наконец, мы собираемся спарсить курс USD/RUB с сайта ЦБ, чтобы использовать его как целевую переменную. Описанные выше данные взаимосвязаны с курсом доллар-рубль, именно поэтому мы считаем, что можно попробовать обучить модель предсказывать его по этим индикаторам состояния рынка.

Парсинг описанных выше данных находится в файлах financial_parser.py (будет использоваться в файле step03_preprocessing.ipynb) и step02_parser.ipynb

## Описание машинного обучения
В проекте ради эксперимента мы планируем попробовать обучить все известные нам регрессоры (линейную, случайный лес и т.д.).

## Описание гипотез
- Разница между ценой открытия и закрытия IMOEX статистически не значима

To be continued...

