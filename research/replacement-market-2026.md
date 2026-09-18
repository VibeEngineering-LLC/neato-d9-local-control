# Рынок замены Neato: роботы-пылесосы с полностью локальным управлением (сентябрь 2026)

**Дата отчёта:** 17.09.2026
**Повод:** облако Neato отключено 30.11.2025, роботы D8/D9/D10 потеряли управление
(зафиксировано в `device-facts.md`).
Задача — найти замену, которая не может быть отключена производителем.

**Правило отчёта:** каждое фактическое утверждение сопровождается URL и датой. «Дата источника» —
это либо дата, проставленная на самой странице, либо дата, когда страница была прочитана мной
(17.09.2026); там, где на странице даты нет, так и написано. Утверждений «обычно так» и
«вероятно» в отчёте нет; чего не нашёл — вынесено в раздел «Что проверить не удалось».

---

## 0. Краткий вывод

1. **Единственный способ получить робота, который физически не зависит от облака производителя, —
   Valetudo** (рутованная прошивка + локальный веб-интерфейс + MQTT). 48 моделей в исчерпывающем списке
   на 17.09.2026.
2. **Рутование без вскрытия корпуса не существует ни у одной модели, продающейся новой в 2026.**
   Софтовый рут «по Wi-Fi» есть только у Roborock S5 и Xiaomi V1 (выпуска до 03.2020) — это
   роботы 2017–2019 годов, доступные только б/у. У всех актуальных моделей нужно как минимум снять
   пластиковую крышку монтажным лопаткой (pry tool). **Пайка не нужна нигде** из актуальных вариантов;
   гарантийные пломбы у Dreame/Eureka остаются целы.
3. **Самый лёгкий рут среди продающихся новыми — Eureka (Midea) J15 Max Ultra / J15 Pro Ultra /
   J15 Ultra / J12 Ultra**: Linux-ноутбук + кабель micro-USB + пластиковая лопатка, без UART-адаптера
   и без дополнительной платы.
4. **Официального локального API «из коробки» с уровнем управления, сравнимым с Valetudo, в 2026 нет.**
   Matter (RVC) даёт старт/стоп/док/выбор зон локально, но не карты и не настройки; Roborock при потере
   интернета блокирует свой локальный API; Ecovacs лечится только самодельным сервером Bumper.
5. **D-образный корпус в 2026 выпускает только Vorwerk (Kobold VR7)** — и это чистое облако, то есть
   ровно тот риск, от которого мы уходим. Ближайшие геометрические аналоги — «квадратные» Ecovacs
   DEEBOT X-серии и D-образные швабры Dreame W10/W10 Pro.

---

## 1. Valetudo — список поддерживаемых моделей на 17.09.2026

**Первоисточник:** <https://valetudo.cloud/pages/general/supported-robots/> — прочитано 17.09.2026,
даты последнего обновления на странице нет.
Страница сама объявляет себя исчерпывающей, дословно:

> «Please note that this list is exhaustive. These are the supported robots.
> Robots not on this list are not supported by Valetudo.»

Из этого прямо следует: **Dreame X50 Ultra, Roborock Saros/Qrevo, Ecovacs, Narwal, Eufy, iRobot —
не поддерживаются Valetudo** (их нет в списке).

Там же — объяснение, почему новых вендоров почти не добавляется (важно для оценки риска):

> «These security flaws are all 0days… With a public root release, these get burned and usually
> quickly fixed by the vendors, making finding a working exploit chain for newer models after the
> release harder or sometimes even impossible.»

Актуальность проекта подтверждается релизами: последний — **2026.08.0 от 03.08.2026**
(API GitHub, `https://api.github.com/repos/Hypfer/Valetudo/releases`, запрос 17.09.2026;
человекочитаемо — <https://github.com/Hypfer/Valetudo/releases>). Предыдущие: 2026.07.0 (23.07.2026),
2026.05.0 (22.05.2026), 2026.02.0 (25.01.2026), 2026.01.0 (29.12.2025).

### 1.1. Ключевое различение: что именно требуется физически

Все формулировки ниже — дословно со страницы supported-robots и со страниц установки
(<https://valetudo.cloud/pages/installation/dreame/>, `/midea/`, `/roborock/`), прочитаны 17.09.2026.

| Группа (кол-во моделей) | Модели | Что нужно физически | Пайка | Пломбы |
|---|---|---|---|---|
| **A. Софтовый рут по сети** (2) | Roborock S5; Xiaomi V1 выпуска **до 2020-03** | «only requiring a Laptop» — OTA по Wi-Fi, ничего не вскрывать | нет | «All warranty seals stay intact» |
| **B. Dreame UART** (12) | Xiaomi 1C, 1T, P2148, Vacuum-Mop 2 Ultra, X10 Plus; Dreame D9, D9 Pro, F9, L10 Pro, Z10 Pro, W10; MOVA Z500 | Снять верхнюю пластиковую крышку лопаткой → 16-контактный debug-разъём; Dreame Breakout PCB + USB-UART 3.3 В + USB-флешка | нет (разъём — штекерный) | «All warranty seals stay intact» |
| **C. Dreame Fastboot** (12) | Dreame W10 Pro, L10s Ultra, D10s Pro, D10s Plus, L10s Pro Ultra Heat, L20 Ultra (только R2394), X30 Ultra, L40 Ultra, X40 Ultra, X40 Master; MOVA S20 Ultra, P10 Pro Ultra | То же вскрытие крышки + Breakout PCB + Debian 13 Live + `sunxi-tools` + `fastboot` | нет | «All warranty seals stay intact» |
| **D. Roborock FEL** (6) | S6 Pure, S4 Max, S5 Max, S7, S7 Pro Ultra, Q7 Max | «full disassembly including destruction of all warranty seals»; замкнуть тест-пойнт TPA 17 на нижней стороне платы | нет | **уничтожаются** |
| **E. Roborock Vinda / init override** (3) | S4, S6, Xiaomi V1 выпуска после 2020-03 | «full disassembly of the robot as well as soldering some wires which will void your warranty» (Vinda) | **да** (Vinda) | уничтожаются |
| **F. 3irobotix CRL-200S по ADB** (7) | Xiaomi Vacuum-Mop P; Viomi V6, Viomi SE; Conga 3290, 3790; Proscenic M6 Pro; Commodore CVR 200; IKOHS Netbot LS22 | «Linux Laptop and a micro USB cable»; «It might be required to remove the battery but that can be done without touching any warranty seals» | нет | целы |
| **G. Midea/Eureka по ADB** (6) | Eureka J15 Max Ultra, J15 Pro Ultra, J15 Ultra, J12 Ultra, E20 Evo Plus, E20 Plus | «Linux Laptop and a micro USB cable»; порт micro-USB внутри: «Regardless of model, this will require some plastic Pry Tool» | нет | «All warranty seals stay intact» |

Итого 48 моделей (Xiaomi 7, Dreame 16, MOVA 3, Roborock 9, Viomi 2, Eureka 6, Cecotec 2,
Proscenic 1, Commodore 1, IKOHS 1). Пересчитано по разделам страницы 17.09.2026.

**Вывод по ключевому различению:** роутинг «по Wi-Fi без вскрытия» доступен **только** для группы A —
то есть для Roborock S5 и старых Xiaomi V1. Для всего, что можно купить новым в 2026, минимальная
инвазивность — «снять верхнюю крышку пластиковой лопаткой», без пайки и без потери пломб.
Полная разборка с пайкой осталась только у старых Roborock (группы D, E).

### 1.2. Что ещё продаётся новым в 2026, а что только б/у

**Первоисточник:** <https://valetudo.cloud/pages/general/buying-supported-robots/>, на странице явно
написано: «This was last updated 2025-12-31» (прочитано 17.09.2026).

Рекомендация автора проекта дословно:

> «Probably a Dreame X40 or L40. If you really do absolutely not want to go the PCB rooting route
> required for all Dreames, get the Eureka J15 Max instead. If you're on a budget, check for offers
> for the L10s Ultra or J15 Pro Ultra respectively.»

Продаётся новым (на той же странице автор даёт партнёрские ссылки на Amazon DE, то есть товар
в рознице присутствует): **Dreame X40 Master, Dreame X40 Ultra, Eureka J15 Max Ultra, Eureka J15 Pro
Ultra, Eureka J15 Ultra, Eureka J12 Ultra, Eureka E20 Evo Plus, Eureka E20 Plus**. Про L20 Ultra там же:
«for some inexplicable reason, in DE in 2025, you can still get it new in box. You shouldn't, but you can».

Только б/у либо «если случайно попалось» (цитаты оттуда же):
* Roborock V1 — «absolutely no reason to buy it in 2025 due to its lack of persistent maps»;
* Roborock S5 — «Cheap (used), easy to root… if you're a person that proudly drives a 20 year old station wagon»;
* Roborock S6, S4 и пр. — «If you have one, guess they're rootable. Otherwise, not worth bothering with»;
* Dreame D9 (Pro), D10s Pro/Plus — «No need to buy them new»;
* Roborock Q7 Max — новый экземпляр с высокой вероятностью не рутуется (см. §2.2).

Отдельно важное предупреждение о сроке жизни (дословно):

> «if you want to buy something that will last for a decade or so, your options are a nullpointer…
> Specifically, replacement parts availability is the key limiting factor.»

---

## 2. Dreame и Roborock: что рутуется без пайки, что производитель закрыл

### 2.1. Dreame — без пайки, но со вскрытием крышки

**Источник:** <https://valetudo.cloud/pages/installation/dreame/>, прочитано 17.09.2026 (даты на странице нет).

* Доступ к 16-контактному debug-разъёму: «For all round-shaped dreames, this means removing the top
  plastic cover with a pry tool or your fingers»; «If your Dreame is a D-shaped Mop such as the W10,
  simply take out the dustbin and open the rubber flap in front of that port».
* Breakout PCB (<https://github.com/Hypfer/valetudo-dreameadapter>) формально необязателен, но:
  «While the Dreame Breakout PCB greatly simplifies the process, it is not strictly required but just
  highly recommended to avoid people breaking the connector».
* Secure boot: «on some p-dreames… Dreame introduced a secure boot scheme with a key burned into the
  SoC»; «you MUST defeat the secure boot mechanism before making any modifications to the filesystem
  or else you will brick your robot». Обход делает `install.sh` из сборки dustbuilder
  (<https://builder.dontvacuum.me>, доступен 17.09.2026).
* Изменение 2026 года, дословно: «Previously, this guide used a proprietary vendor tool to push the
  payload onto the robot. **In 2026**, we've managed to switch to the much cleaner and much FOSS-er
  `sunxi-tools` instead.» То есть метод fastboot в 2026 стал чище, а не закрылся.
* Модели с `Secure Boot: yes` (со страницы supported-robots): Xiaomi Vacuum-Mop 2 Ultra (с FW 1167),
  X10 Plus, L10 Pro (с FW 1138), Z10 Pro (с FW 1156) и вся группа fastboot.

**Что Dreame закрыл:**
* **L20 Ultra** — дословно: «There are two different robots out there that both are called L20 Ultra
  and look *identical*. However, only **ONE** of those is rootable. Look for a serial starting with
  R2394. If it is starting with R2253, it is **NOT** rootable.» На странице покупки — «the majority
  of the units in the market are of the non-rootable rockchip variety».
* **L10/Z10** — «Replacement PCBs aren't rootable» (страница покупки, 2025-12-31).
* **X50 Ultra и всё, что вышло после X40** — в исчерпывающем списке отсутствуют, значит не
  поддерживаются (вывод из процитированного выше утверждения об исчерпывающести списка,
  прочитано 17.09.2026). Публичного руткита для X50 я не нашёл — см. «Что проверить не удалось».
* Побочный эффект новых прошивок: «If Valetudo doesn't want to auto-detect the robot, and it was made
  around **08/2025 or later**, Dreame might've switched to negative deviceIds» — обход описан там же
  (правка `/mnt/private/ULI/factory/did.txt`).

### 2.2. Roborock — фактически закрыт

**Источник:** <https://valetudo.cloud/pages/installation/roborock/> и раздел Roborock на supported-robots,
прочитано 17.09.2026.

* Самый новый поддерживаемый Roborock — **Q7 Max** (2022 г.). Ничего новее в списке нет.
* Дословное предупреждение с датой прямо в тексте: «**2024-09-28 Update** Starting with robots
  manufactured somewhere around Q2 2024, Roborock switched to SkyHigh-brand NAND on their newly
  produced Q7 Max… we haven't been able to get the rooting procedure working with said NAND. Thus, if
  you pick up a factory new Q7 Max then chances are that it's not rootable anymore… You'll only find
  out that it's SkyHigh NAND once you've disassembled the robot and thus can't return it to the seller.»
* OTA-рут закрыт прошивкой: «robots made after 2020-03 come with a non-local-OTA capable recovery
  firmware version».
* Методы для всех оставшихся Roborock требуют полной разборки; Vinda дополнительно требует пайки
  («soldering some wires which will void your warranty»); FEL пайки не требует, но требует замыкания
  TPA 17 и уничтожает пломбы.

**Вывод:** покупать Roborock новым ради Valetudo в 2026 бессмысленно.

### 2.3. Инструменты и исследователь

* **Dustbuilder** — сборщик рутованных прошивок: <https://builder.dontvacuum.me> (HTTP 200, 17.09.2026).
  Используется и в Dreame-, и в Midea-инструкции.
* **Dustcloud** — <https://github.com/dgiese/dustcloud>, по описанию на <https://dontvacuum.me/>
  (прочитано 17.09.2026) покрывает исходники для «Roborock/Xiaomi robot (v1, s5)», то есть старое поколение.
* **Dennis Giese, список докладов** — <https://dontvacuum.me/talks/>, прочитано 17.09.2026.
  Самый свежий доклад в списке: **NULLcon Goa 2025, 26–28.02.2025, «How Ecovacs robots got hacked and
  what we can learn from it»**. Докладов 2026 года на странице нет.
* **robotinfo.dev** (бывш. `dontvacuum.me/robotinfo/`, 302-редирект) — сравнительная база железа.
  На странице стоит «Last import timestamp: 2024-10-02 03:31:34» (прочитано 17.09.2026), то есть
  **база устарела на два года** и для вопросов 2026 года не годится; ссылку оставляю только как
  справочник по железу старых моделей.
* Форма запроса на поддержку новых моделей: <https://requests.valetudo.cloud> (HTTP 200, 17.09.2026).

---

## 3. Альтернативы с официальным локальным управлением (без взлома)

### 3.1. Matter / RVC — да, локально, но узко

* Home Assistant, документация интеграции Matter: <https://www.home-assistant.io/integrations/matter/>
  (прочитано 17.09.2026). Дословно: «Matter products run locally and always allow local control, with
  device control done without the need for any internet connection or cloud services». Категория
  «Vacuum» в списке поддерживаемых присутствует. Оговорка на той же странице: часть вендоров требует
  завести аккаунт, прежде чем включить Matter на устройстве.
* Управление зонами появилось в Home Assistant **2026.3** — <https://www.home-assistant.io/blog/2026/03/04/release-20263/>
  (дата релиза в URL — 04.03.2026, прочитано 17.09.2026), раздел «Send your vacuum to clean specific
  areas», дословно: «In this release, it's supported by Matter, Ecovacs, and Roborock».
* Стандарт: Service Area Cluster (выбор зон уборки) добавлен в **Matter 1.4**; в **Matter 1.4.2** CSA
  стандартизировала поведение RVC — <https://csa-iot.org/newsroom/matter-1-4-2-enhancing-security-and-scalability-for-smart-homes/>
  (прочитано 17.09.2026).
* **Что Matter НЕ даёт:** построение и редактирование карты, тонкие настройки уборки, телеметрию
  расходников. Зоны в Service Area — это зоны, заведённые в приложении вендора, а не в контроллере.
  Точную границу возможностей по тексту спецификации я не проверял — см. «Что проверить не удалось».
* Модели с Matter (вторичный источник, профильное издание по Matter):
  <https://www.matteralpha.com/news/matter-update-issued-by-roborock-more-models-to-come>
  (прочитано 17.09.2026) — Roborock S8 MaxV Ultra, Saros 10, Saros 10R, Saros Z70, Qrevo Curv,
  Qrevo Edge, Qrevo Master, Qrevo Slim. Проверить этот перечень по сертификационной базе CSA
  не удалось (см. ниже).

**Риск Matter:** сам протокол локален и не может быть «выключен» сервером. Но первичная настройка
робота (карты, зоны) у всех известных мне вендоров идёт через их приложение и облако, поэтому
Matter — это защита от полного «окирпичивания», а не полноценная замена Valetudo.

### 3.2. Roborock — локальный API есть, но заблокирован без интернета

Документация интеграции Home Assistant: <https://www.home-assistant.io/integrations/roborock/>
(прочитано 17.09.2026). Дословно:

> «Despite this integration's IoT class being local polling, cloud access is required for it to work
> just like any other cloud based integration.»

и, что решающе:

> «When the vacuum is disconnected from the internet, it blocks its local API until it can reach the
> Roborock servers.»

**Вывод:** Roborock без облака не работает по замыслу производителя. Сценарий Neato воспроизводим
полностью. Локальный опрос (порт 58867/TCP, 58866/UDP) — оптимизация задержек, а не независимость.

### 3.3. Ecovacs — только через самодельный сервер Bumper

* Документация HA: <https://www.home-assistant.io/integrations/ecovacs/> (прочитано 17.09.2026).
  IoT-класс — Cloud Push, нужен аккаунт Ecovacs. Но: «During setup, you can choose to use a
  self-hosted instance over the cloud servers. Self-hosting comes with some requirements and limitations.»
* Self-hosted реализация — **Bumper**. Оригинал <https://github.com/bmartin5692/bumper> фактически
  заморожен (последний push **05.08.2024**, API GitHub, запрос 17.09.2026). Живой форк —
  <https://github.com/MVladislav/bumper> (последний push **17.09.2026**, 91 звезда). Дословно из README:
  «Bumper is a self-hosted central server for Ecovacs vacuum robots. It replaces the Ecovacs cloud».
  Там же предупреждение: «⚠️ Warning: Branches `main`/`dev` are under active development and may be unstable.»
  Требуется перенаправление DNS `ecovacs.net` на свой сервер и подмена TLS-сертификатов; приложение
  Ecovacs Home с версии 2.4.4+ требует обхода certificate pinning.
* Клиентская библиотека <https://github.com/DeebotUniverse/client.py> — активна (push 17.09.2026).
* Модели, заявленные как работающие с Bumper (README, 17.09.2026): Deebot 900/901, 600, T10 Plus,
  T80 Omni, X1 Omni, X2 Pro Omni, X9 Pro Omni, Ozmo 950 (MQTT); Ozmo 601, 930, M81 Pro (XMPP).

**Оценка:** это не «официальный локальный API», а перехват облака на своём сервере. Устойчивость к
решению вендора — средняя: пиннинг сертификатов в приложении уже ломает схему, и это ломает именно
вендор своими обновлениями.

### 3.4. Xiaomi miIO — локальный протокол, но токен добывается из облака

<https://www.home-assistant.io/integrations/xiaomi_miio/> (прочитано 17.09.2026): IoT-класс —
Local Polling, работа возможна без облака, но токен устройства извлекается либо из аккаунта Xiaomi,
либо из бэкапа приложения. Отдельная оговорка в документации: «Roborock vacuums need to be connected
to the Xiaomi Home app, not the Roborock app». Применимо к старым Xiaomi/Roborock-роботам,
у новых моделей miIO-путь я не проверял.

### 3.5. Open-source робот целиком — есть, но ещё не собирается

**oomwoo** — <https://github.com/makerspet/oomwoo>, Apache-2.0, репозиторий создан **10.06.2026**,
последний push **17.09.2026**, 10 928 звёзд (API GitHub, запрос 17.09.2026). Описание проекта —
<https://makerspet.com/blog/building-an-open-source-robot-vacuum-meet-oomwoo/> (пост от 14.06.2026,
прочитано 17.09.2026): Raspberry Pi 5 + ROS 2 Nav2 + 2D-LiDAR + собственная плата драйверов на
STM32G070RBT6, целевой бюджет «$100~$200 + Raspberry Pi 5», цель по качеству — «mid-range $500-$600 vacuum».

**Статус на 17.09.2026: собрать нельзя.** По тому же посту не выпущены STL-файлы, прошивка, плата
драйверов, инструкция по сборке и BoM. Как замена «прямо сейчас» не годится; как стратегический
запасной путь — интересен.

---

## 4. D-образная форма корпуса в 2026

**Ответ: серийно D-образный корпус в 2026 выпускает только Vorwerk (Kobold VR7). Второго
производителя я не нашёл.**

* Vorwerk Kobold VR7, официальная страница <https://www.vorwerk.com/de/de/c/home/produkte/kobold/kobold-vr7-saugroboter>
  (HTTP 200, 17.09.2026): D-образный корпус, лазерная навигация, станция самоочистки, только сухая
  уборка. Цена: 999 € по агрегатору <https://geizhals.de/vorwerk-kobold-vr7-saug-wischroboter-a3097314.html>
  (прочитано 17.09.2026), базовая рекомендованная — 1 249 €.
* **Но Kobold VR7 — облачный.** По разведке этого же проекта (`research/kobold-vr7.md`, 15.09.2026)
  управление идёт через официальный Kobold API v2 и требует аккаунта Kobold и настройки через
  фирменное приложение. То есть VR7 воспроизводит ровно тот риск, от которого мы уходим: это тот же
  концерн Vorwerk, который отключил облако Neato 30.11.2025.
* **Геометрические полуаналоги:**
  * **Dreame W10 / W10 Pro** — в документации Valetudo прямо названы «D-shaped Mop»
    (<https://valetudo.cloud/pages/installation/dreame/>, 17.09.2026). Оба поддерживаются Valetudo
    (W10 — UART, W10 Pro — fastboot). Это швабра-робот, а не сухой пылесос класса Neato;
    на странице покупки отдельно отмечено, что у W10 (Pro) «oddly-shaped battery pack» и запчастей
    к нему не найти.
  * **Ecovacs DEEBOT X2 OMNI** и последующие X-модели — «квадратный» корпус со скруглёнными углами и
    плоским передом: официальная страница <https://www.ecovacs.com/us/shop/deebot-robotic-vacuum-cleaner/deebot-x2-omni>
    (HTTP 200, 17.09.2026) прямо называет его «Square Robot Vacuum». Valetudo его не поддерживает;
    локально — только через Bumper (§3.3).
* **Чего я не нашёл:** ни одной новой D-образной модели от Roborock, Dreame (кроме W-серии швабр),
  Eureka/Midea, Narwal, Eufy, iRobot в 2026 году.

### Что вообще означает «класс уборки Neato D8/D9/D10»

По анонсу линейки (AppleInsider, **06.09.2020**,
<https://appleinsider.com/articles/20/09/06/neatos-d8-d9-d10-robot-vacuums-boast-laser-assistance-siri-shortcut-support>,
прочитано через WebFetch 17.09.2026; прямой `curl` к домену отдаёт 403):
LaserSmart-навигация (LIDAR) у всех трёх; «edge-to-edge cleaning with the widest brush available in
the robot vacuum market»; D8 — 90 минут работы, D9 — до 120 минут и HEPA-подобный фильтр 99,5 %,
D10 — 150 минут и True HEPA 99,7 % до 0,3 мкм. Мойки пола и станции автовыгрузки в линейке нет.

Отсюда практический вывод: **любой из рекомендованных ниже роботов 2023–2025 годов превосходит
D8/D9/D10 по сухой уборке** (LIDAR + значительно большая мощность всасывания + станция самовыгрузки),
и все они дополнительно умеют мыть пол. Единственное, в чём Neato объективно лучше, — геометрия
захода в углы за счёт D-формы и щётки во всю ширину; численного сравнения «D-форма против круглой»
из лабораторного первоисточника я не нашёл (см. ниже).

---

## 5. Карточки подходящих моделей

Цены — ориентир, взяты из рыночных агрегаторов и листингов на 17.09.2026; они волатильны, это не
котировка. «Риск, что производитель прикроет» оценивается по одному критерию: может ли решение
вендора (отключение сервера, обновление прошивки, смена комплектующих) лишить владельца управления.

### 5.1. Dreame X40 Ultra / X40 Master — рекомендация самого проекта

| Поле | Значение |
|---|---|
| Локальное управление | Valetudo (полностью автономно, вендорское облако вырезано; dustbuilder патчит DNS) |
| Способ рута | Fastboot: снять верхнюю крышку лопаткой → Dreame Breakout PCB в 16-pin разъём → Debian 13 Live + `sunxi-tools` + `fastboot` |
| Вскрытие | Да — верхняя пластиковая крышка. Пайки нет. «All warranty seals stay intact» |
| Home Assistant | Да, MQTT + autodiscovery, без облака (<https://valetudo.cloud/pages/integrations/home-assistant-integration/>, 17.09.2026); карта — Lovelace Valetudo Map Card |
| Цена (ориентир) | ~$900–1 300 в США при запуске, на распродажах опускалась ниже $900 (листинги Amazon и агрегаторы, сверено 17.09.2026) |
| Риск «прикроют» | **Низкий после рута**: облако физически не участвует. Риск до рута — купить экземпляр с новой прошивкой/ревизией; риск в перспективе — прекращение выпуска запчастей |
| Источник | <https://valetudo.cloud/pages/general/supported-robots/>, <https://valetudo.cloud/pages/general/buying-supported-robots/> (обновлена 31.12.2025) |

Цитата рекомендации: «Probably a Dreame X40 or L40… Newest Dreames supported by Valetudo. Best
features and quality sw/hw you can get right now».
⚠ Ловушка названий, дословно: L40 Ultra «is **not sold** as the L40 Ultra **AE** nor as the
L40**s Pro Ultra**»; более того, «Dreame has started selling "L40" that are actually just rebadged
"L10s Pro Gen3" in some markets».

### 5.2. Eureka J15 Max Ultra — самый лёгкий рут из новых

| Поле | Значение |
|---|---|
| Локальное управление | Valetudo |
| Способ рута | ADB по micro-USB с Linux-ноутбука (Debian 13 Live). Плата-переходник и UART-адаптер **не нужны** |
| Вскрытие | Минимальное: «Regardless of model, this will require some plastic Pry Tool» — только чтобы добраться до micro-USB. Пайки нет, «All warranty seals stay intact» |
| Home Assistant | Да, MQTT + autodiscovery |
| Цена (ориентир) | MSRP ~$1 199, фактические предложения от ~$650–900 (листинги Amazon/агрегаторы, 17.09.2026) |
| Риск «прикроют» | **Низкий после рута.** Но: «every firmware update has the potential to come with new locks, meaning that you should **not ever** update using the vendor app/cloud» — то есть до рута робот нельзя подключать к фирменному приложению |
| Источник | <https://valetudo.cloud/pages/installation/midea/>, <https://valetudo.cloud/pages/general/supported-robots/> (17.09.2026) |

Оценка автора проекта: «Easy root. Alright if competitively priced. Has all the features on paper.
Software could still use polish» (страница покупки, 31.12.2025).

### 5.3. Eureka J15 Pro Ultra — бюджетный вариант того же пути

| Поле | Значение |
|---|---|
| Локальное управление | Valetudo |
| Способ рута | тот же ADB по micro-USB, лопатка, без пайки |
| Вскрытие | минимальное, пломбы целы |
| Home Assistant | Да, MQTT |
| Цена (ориентир) | ~$700 и ниже на акциях (листинги Amazon, 17.09.2026) |
| Риск «прикроют» | низкий после рута; те же условия «не обновлять через приложение вендора» |
| Источник | те же страницы Valetudo, 17.09.2026 |

### 5.4. Dreame L10s Ultra — б/у и «на бюджете», с оговоркой по надёжности

| Поле | Значение |
|---|---|
| Локальное управление | Valetudo, метод fastboot |
| Вскрытие | верхняя крышка, Breakout PCB, без пайки, пломбы целы |
| Home Assistant | Да, MQTT |
| Цена (ориентир) | ниже X40; конкретную цифру не фиксирую — на 17.09.2026 в основном вторичный рынок |
| Риск «прикроют» | низкий после рута, но **высокий риск железа**: дословно — «Dock freshwater supply tends to break if you don't use it. We're seeing elevated battery failure rates after 2y» |
| Источник | <https://valetudo.cloud/pages/general/buying-supported-robots/> (31.12.2025) |

### 5.5. Roborock Saros/Qrevo с Matter — если вскрывать корпус категорически нельзя

| Поле | Значение |
|---|---|
| Локальное управление | Только Matter: старт/стоп/док/зоны локально через Home Assistant |
| Способ | Штатный, без взлома; требуется настройка через приложение Roborock и облако |
| Вскрытие | нет |
| Home Assistant | Да, через интеграцию Matter (локально); родная интеграция Roborock — облачная |
| Цена (ориентир) | Qrevo-класс — около $850 и выше на распродажах; Saros — дороже (листинги, 17.09.2026) |
| Риск «прикроют» | **Высокий.** Официально: «When the vacuum is disconnected from the internet, it blocks its local API until it can reach the Roborock servers» (<https://www.home-assistant.io/integrations/roborock/>, 17.09.2026). Matter-команды переживут отключение облака, карты и настройки — нет |
| Источник | <https://www.home-assistant.io/integrations/matter/>, <https://www.home-assistant.io/blog/2026/03/04/release-20263/>, <https://www.matteralpha.com/news/matter-update-issued-by-roborock-more-models-to-come> |

**Итоговая рекомендация из трёх карточек:**
1. Если важнее всего независимость и не пугает снятие крышки — **Dreame X40 Ultra / L40 Ultra**.
2. Если хочется минимума манипуляций с железом при той же независимости — **Eureka J15 Max Ultra**.
3. Если вскрытие корпуса недопустимо в принципе — **Roborock с Matter**, с прямым пониманием, что
   при отключении облака останутся только базовые команды, а сценарий Neato повторится частично.

---

## 6. Что проверить не удалось

1. **Сертификационная база CSA по Matter-пылесосам.** Фильтр на
   <https://csa-iot.org/csa-iot_products/> через WebFetch вернул «No Entries Found» (поиск на сайте
   работает только в браузере с JS). Перечень Matter-моделей Roborock взят из профильного издания
   matteralpha.com, а не из реестра CSA. Не подтверждено первоисточником.
2. **Точный набор кластеров и ограничений Matter RVC** (что именно можно и нельзя: карты, no-go зоны,
   мощность). Текст спецификации Matter 1.4/1.4.2 (PDF на csa-iot.org) я не разбирал; утверждение
   «Matter не даёт карт» опирается на документацию Home Assistant и пресс-релиз CSA, а не на спецификацию.
3. **Публичный рут для Dreame X50 Ultra / X60.** Их отсутствие в списке Valetudo доказывает только
   отсутствие поддержки Valetudo. Существует ли где-то ещё рабочий рут — не нашёл ни подтверждения,
   ни опровержения.
4. **Численное сравнение эффективности D-образного корпуса против круглого** (сколько реально
   теряется в углах). Лабораторного первоисточника не нашёл — только маркетинговые формулировки
   производителей.
5. **Официальный локальный API у Dreame и Eureka в стоковой прошивке.** Целенаправленно не искал
   документации вендоров: для наших целей вопрос снимается рутом. Утверждать, что его нет, не могу.
6. **Актуальные розничные цены в РФ.** Все цены в отчёте — с рынков США/ЕС. Российские цены,
   наличие и гарантия не проверялись.
7. **Доклады Dennis Giese за 2026 год.** На <https://dontvacuum.me/talks/> (17.09.2026) самый свежий —
   NULLcon Goa, февраль 2025. Означает ли это паузу в исследованиях или просто необновлённую страницу —
   не знаю.
8. **Дата последнего обновления страницы supported-robots.** Явной даты на странице нет; косвенные
   признаки актуальности — упоминание прошивок «08/2025 or later» и фраза «In 2026» на странице установки Dreame.

---

## LESSONS

1. **Ожидал**, что у современных роботов есть путь рута «по воздуху», как в 2018-м у Roborock S5.
   **Оказалось**, что софтовый рут остался только у моделей выпуска до марта 2020, а всё
   продающееся сегодня требует минимум снятия верхней крышки; зато пайка ушла почти отовсюду —
   это другое измерение сложности, и его легко перепутать с «сложно». **Обход:** различать в отчётах
   три независимых параметра — вскрытие корпуса, пайка, потеря пломб; одним словом «инвазивность» они не описываются.
2. **Ожидал**, что «локальный API» в документации означает независимость от облака.
   **Оказалось**, что Roborock прямым текстом блокирует собственный локальный API, когда робот не
   видит серверов вендора, — то есть «local polling» в терминологии Home Assistant это про транспорт,
   а не про автономность. **Обход:** проверять не ярлык IoT-класса, а явную фразу о поведении
   устройства при отсутствии интернета.
3. **Ожидал** найти актуальные данные в сравнительной базе `dontvacuum.me/robotinfo`.
   **Оказалось**, что домен переехал на robotinfo.dev, а импорт данных там датирован 02.10.2024 —
   база отстаёт на два года, и построенный на ней ответ о «моделях 2026» был бы неверным при
   правдоподобном виде. **Обход:** первым делом искать на странице метку времени импорта/обновления
   и явно писать её в отчёт, а не только URL.
