# Проект
**План**
- [Шаг 1. Выбор темы](https://github.com/evelinakolomoets/andan_project/blob/main/README.md#шаг-1-выбор-темы)
- [Шаг 2. Сбор данных](https://github.com/evelinakolomoets/andan_project/blob/main/README.md#шаг-2-сбор-данных)
- [Шаг 3. Предварительная обработка](https://github.com/evelinakolomoets/andan_project/blob/main/README.md#шаг-3-предварительная-обработка)
- [Шаг 4. Визуализация](https://github.com/evelinakolomoets/andan_project/blob/main/README.md#шаг-4-визуализация)
- [Шаг 5. Создание новых признаков](https://github.com/evelinakolomoets/andan_project/blob/main/README.md#шаг-5-создание-новых-признаков)
- [Шаг 6. Гипотезы](https://github.com/evelinakolomoets/andan_project/blob/main/README.md#шаг-6-гипотезы)
- [Шаг 7. Машинное обучение](https://github.com/evelinakolomoets/andan_project/blob/main/README.md#шаг-7-машинное-обучение)

**Команда**
- Коломоец Эвелина
- Нагорская Мария
- Сомонов Данил 

## Шаг 1. Выбор темы
Рассматриваются данные с 2008 по 2023 год.

**План сбора данных:**

Спарсить:
- ключевую ставку ЦБ РФ и ФРС (индикаторы монетарной политики)
- цену золота (динамика цен защитного актива) с сайта ЦБ, 
- значение индекса IMOEX с сайта Московской биржи (индикатор состояния ключевых компаний российского рынка; кроме того, по нему можно отслеживать негативный новостной фон)
- инфляцию РФ и США 

Все эти показатели либо отражают макроэкономическую ситуацию и состояние финансового рынка в РФ, либо представляют собой те признаки, которые могут на это повлиять.

Категориальными признаками будут мягкая или жесткая денежная кредитная политика в РФ и в США (новый признак: создадим на основе ставки и инфляции), а также рабочий/нерабочий день (парсим производственный календарь). 

Наконец, мы собираемся спарсить курс USD/RUB, чтобы использовать его как целевую переменную. Описанные выше данные взаимосвязаны с курсом доллар-рубль, именно поэтому мы считаем, что можно попробовать обучить модель предсказывать его по этим индикаторам состояния рынка.


## Шаг 2. Сбор данных
> Файл этого шага: [step02_parser.ipynb](https://github.com/evelinakolomoets/andan_project/blob/main/step02_parser.ipynb)

**Результаты**:
- Курс USDRUB из XML Банка России
- Ключевая ставка с сайта Банка России
- Учетная ставка с сайта ФРС
- Цена золота из XML Банка России
- Значение IMOEX в момент открытия и закрытия торгов из ISS Московской Биржи
- ИПЦ с сайта Росстата
- ИПЦ с сайта St. Louis FED
- Производственный календарь

Парсер вынесен в файл [`financial_parser.py`](https://github.com/evelinakolomoets/andan_project/blob/main/financial_parser.py), который будет использован на следующем шаге.

## Шаг 3. Предварительная обработка
> Файл этого шага: [step03_preprocessing.ipynb](https://github.com/evelinakolomoets/andan_project/blob/main/step03_preprocessing.ipynb)

**Описание переменных**:

* `gold` — Цена золота за грамм на определенную дату, в рублях
* `cb_key_rate` — Ставка Центрального банка РФ на определенную дату, в %
* `fed_rate` — Ставка Федеральной резервной системы США на определенную дату, в %
* `imoex_open` — Значение индекса IMOEX (Мосбиржи) на момент открытия торгов, в рублях
* `imoex_close` — Значение индекса IMOEX (Мосбиржи) на момент закрытия торгов, в рублях
* `ru_cpi` — Значение индекса потребительских цен (ИПЦ) РФ на конец месяца по отношению к предыдущему месяцу (н.: май к апрелю), в %
* `us_cpi` — Значение индекса потребительских цен (ИПЦ) США на конец месяца по отношению к предыдущему месяцу (н.: май к апрелю), в %
* `workday` - Рабочий или выходной день в РФ в определенную дату, принимает 2 значения: `workday` и `day off`

**Целевая переменная:** `usdrub` — Курс доллар/рубль на определенную дату, в рублях

**Добавленные на этом этапе переменные:**
- `first_workday` - первый рабочий день после выходных. Бинарный признак, принимает значение 0 или 1. Посчитан при помощи `workday`
- `second_workday` - второй рабочий день после выходных. Бинарный признак, принимает значение 0 или 1. Посчитан при помощи `workday`

## Шаг 4. Визуализация
> Файл этого шага: [step04_plots.ipynb](https://github.com/evelinakolomoets/andan_project/blob/main/step04_plots.ipynb)

![output_17_0](https://github.com/evelinakolomoets/andan_project/assets/103259249/c1deb30f-632e-4def-a81d-d5ecc8658e89)


## Шаг 5. Создание новых признаков
> Файл этого шага: [step05_new_features.ipynb](https://github.com/evelinakolomoets/andan_project/blob/main/step05_new_features.ipynb)

**Добавленные на этом этапе переменные:**
- `imoex_vol` - Изменение значения индекса Мосбиржи, в рублях. Посчитано при помощи `imoex_open` и `imoex_close`
- `ru_monetary` - Разница между годовой инфляцией в России, посчитанной через месячный ИПЦ (экстраполированный на год), и ставкой Банка России, в %. Посчитана при помощи `ru_cpi` и `cb_key_rate`
- `us_monetary` - Разница между годовой инфляцией в США, посчитанной через месячный ИПЦ (экстраполированный на год), и ставкой Федеральной резервной системы, в %. Посчитана при помощи `us_cpi` и `fed_rate`

## Шаг 6. Гипотезы
> Файл этого шага: [step06_hypotheses.ipynb](https://github.com/evelinakolomoets/andan_project/blob/main/step06_hypotheses.ipynb)

Гипотезы проверялись на уровне значимости 5%. 

**Проверяемые гипотезы:**
Гипотезы, которые проверялись при помощи статистических тестов:
- Разница между значением открытия и закрытия IMOEX статистически не значима

Проверялась при помощи t-теста, нулевая гипотеза о равенстве матожиданий цен открытия и закрытия не отверглась
- Инфляции не существует (отклонение ИПЦ от 100 статистически не значимо)

Проверялась при помощи теста Уилкоксона. Нулевая гипотеза о несуществовании инфляции отверглась для России, но не отверглась для США. Однако для США отверглась нулевая гипотеза о несуществовании дефляции
- Золото, доллар и индекс Мосбиржи (реплицировав его структуру) выгодно брать в "лонг" (Математическое ожидание доходностей неотрицательно)

Тоже проверялись при помощи теста Уилкоксона. Нулевая гипотеза о неубыточности вложений не отверглась для всех трех инструментов.

![output_61_0](https://github.com/evelinakolomoets/andan_project/assets/103259249/0e8ac28d-37f6-4297-adfa-c31cc08f4cf1)

Гипотезы, которые проверялись при помощи машинного обучения (модели LASSO):
- Самые значимые признаки при предсказывании курса доллар рубль - это цена золота и цена открытия IMOEX.

| Признак | `us_monetary` | `imoex_close` | `ru_cpi` | `workday` | `first_workday` | `second_workday` | `imoex_vol` |
|---------|---------------|---------------|----------|-----------|-----------------|------------------|-------------|
| Вес     | -2.021        | -1.647        | 0.083    | 0.19      | 0.386           | 0.39             | 0.544       |

| Признак | `ru_monetary` | `fed_rate` | `us_cpi` | `cb_key_rate` | `gold` | `imoex_open` |
|---------|---------------|------------|----------|---------------|--------|--------------|
| Вес     | 1.174         | 2.099      | 3.46     | 6.016         | 6.193  | 17.681       |

*_Значения округлены до 3 знаков после запятой_

Да, наибольший вклад в предсказание таргета вносят gold и imoex_open, поскольку имеют наибольшие (по модулю) веса.


## Шаг 7. Машинное обучение
> Файл этого шага: [step07_ml.ipynb](https://github.com/evelinakolomoets/andan_project/blob/main/step07_ml.ipynb)

В проекте ради эксперимента мы попробовали обучить все известные нам регрессоры: 
- kNN-регрессия
- линейная регрессия
- LASSO регрессия
- Ridge регрессия
- ElasticNet регрессия
- решающее дерево
- случайный лес
- CatBoost
- LightGBM

Мы рассмотрели наиболее популярные метрики для задач регрессии:
- $MSE$ - показывает квадратичную ошибку регрессора, сильно штрафует за большие ошибки. Чем меньше, тем лучше модель
- $MAE$ - показывает абсолютную ошибку регрессора, менее чувствительна к выбросам, чем $MSE$. Качественно - показывает, на сколько рублей в среднем ошибается модель. Чем меньше, тем лучше модель
- $R^2$ - показывает, какая доля дисперсии в таргете объясняется независимыми переменными. Чем больше, тем лучше модель

Лучше всего себя показали случайный лес, CatBoost и LightGBM. Взвесив результаты и издержки, необходимые для их получения, лучшей моделью был выбрали CatBoostRegressor. 

**Метрики на тестовой выборке:**
- $MSE$: 0.9616256353003538
- $MAE$: 0.5960882326305699
- $R^2$: 0.9969981831519741

Выходит, что в среднем модель ошибается менее, чем на рубль - только на 60 копеек, что считаем достойным результатом. 

![График истинных и предсказанных моделью значений таргета](https://github.com/evelinakolomoets/andan_project/assets/103259249/d3996ff9-c6b6-4847-9279-ac03d0aeb180)


