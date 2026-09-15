# Vacuula server — self-hosted облако для Gen4 (РЕШЕНИЕ НА ПОДХОДЕ)

Источники (прочитано лично 2026-09-15): сабреддит r/NeatoRobotics (через Chrome) и Discord-сервер
**«Vacuula — formerly Brainslug»** (`discord.gg/PAgwhWvyD8`, оператор — участник, залогинен). Это то же
сообщество, что делает `vacuula/fang`.

## Главное — переворачивает вывод «всё тупик»

Сообщество разрабатывает **vacuula server** — self-hosted замену умершего облака Neato, размещаемую в своей
локальной сети. Даёт локальное управление роботом без зависимости от Vorwerk. **Явно заявлена поддержка
Gen4 (D800/D8/D9/D10)** — то есть нашего D9.

Статус (из канала #updates, автор Philip2809):
- 29.06.2026: «Vacuula server is coming». Прямо: «**Do you have a Gen4 (D800, D8, D9, D10)…? DON'T THROW IT
  OUT! We will try to help you repair it when the server is out!**»
- 30.08.2026: «hope to have a version out by **18th of September** 2026, possibly earlier. Stay tuned!»
- На 15.09.2026 более свежих сообщений в #updates нет → релиз ожидается ~18.09.2026 (через ~3 дня).

Владелец D9 (ChuckG) в #gen4 спросил «можно ли завести D9?» — ответ модератора (jk): «Yes! The new vacuula
server, hopefully ready soon, is expected to support gen4 robots.»

## Дорожная карта проекта (из #project-status, Philip2809)

- **Version 1** — базовое локальное управление (Neato cleaning logic). Готово для gen1–3.
- **Version 2** — ROS2 + Neato гибрid: nogo-линии, зональная уборка (ETA март 2026). Ограничение: если робот
  выходит за зону, его можно только «вернуть».
- **Version 3** — полностью кастомная навигация ROS2 для любого lidar-пылесоса (future).
- Задержки объяснены security implications / responsible disclosure (работают с вендором, bug bounty вместо
  судов).

## Временные обходы для Gen4 (пока сервер не вышел) — из #gen4

- **Запуск уборки трюком:** reboot робота и СРАЗУ нажать кнопку play — стартует уборка (но в eco-режиме;
  тонкий тайминг, привязан к зелёным пульсам светодиода; с нескольких попыток). Позволяет запускать уборку
  без облака уже сейчас.
- Известная болячка D10: перед каждым заказом уборки робот нужно перезагружать (следствие отсутствия сервера).

## Аппаратные факты сообщества (для serial/UART-вектора)

- **UART-пины — за передним бампером**; распиновка выложена в этом Discord (канал hw-hacking / gen4).
  Root по UART на Gen4 пока НИКТО не получил (подтверждает `serial-hardware-vector.md`).
- **Recovery mode по USB-C** (reddit, пост u/AppropriatePear8302, D8): при подключении по USB-C робот
  поднимается как MTP-устройство `USB\VID_1D6B&PID_0100` (Linux USB Gadget), «Neato Robot / SW Update»,
  версия `1.7.0-2933` (та же, что у нашего D9). Цепочка Bootloader→kernel→MTP-update жива, Neato main app —
  FAIL. SW Update folder ждёт ПОДПИСАННЫЙ firmware package (произвольные файлы отклоняет). ADB/serial/SSH/
  RNDIS по USB — выключены.

## Что это значит для нашего D9

Управление D9 БУДЕТ возможно — не через мёртвое облако Neato и не через RE в одиночку, а через **vacuula
server** сообщества, релиз на днях. **Практический план: дождаться релиза (~18.09.2026), следить за #updates
в Discord, затем поставить vacuula server по их инструкции.** Это неинвазивно и не требует вскрытия.

Резервные варианты, если сервер задержится или не подойдёт: трюк reboot+play (запуск уборки уже сейчас);
ESP32 на кнопку; brain-transplant (deep-research-summary.md).

## Ссылки

- Discord: https://discord.gg/PAgwhWvyD8 (Vacuula — formerly Brainslug)
- fang: https://github.com/vacuula/fang
- reddit-пост про recovery mode: r/NeatoRobotics, «Neato D8 Linux recovery mode found after cloud shutdown»
  (comments/1u1y4rv).
