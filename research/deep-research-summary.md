# Глубокий научный разбор — итог (2026-09-15)

Запущен по команде оператора. Полный разбор всех векторов локального управления Neato D9 (Gen4)
с академическими источниками. Ниже — сжатый итог; каждый пункт подтверждён источником.

## Главное

**Готового решения для локального управления D8/D9/D10 не существует ни у кого** — подтверждено самими
мейнтейнерами (fang, neato-brainslug). Причина: Gen4 = подписанная прошивка + secure boot + залоченная
serial-консоль; старый беспарольный моторный serial-API (D3–D7) на новой плате наружу НЕ выведен.

**Важная поправка к источникам:** диссертация и доклады **Jiska Classen** (DEF CON 27 / WOOT'19,
CVE-2018-20785) — про **ПРЕДЫДУЩЕЕ поколение** (BotVac Connected / Vorwerk VR200-300 на **TI AM335x, QNX**),
НЕ про Gen4 (Linux/i.MX). Их cold-boot secure-boot-обход давно пропатчен и к D9 неприменим. Ценны для
понимания экосистемы/облака, но не как рецепт для D9.

## Ранжирование векторов (для владельца одного D9, от реалистичного к тупику)

1. **ESP32 на физическую кнопку Start/Stop** — усилия низкие, риск минимальный, обратимо. Даёт только
   «запустить/остановить уборку» (в т.ч. из Home Assistant), без карт и телеметрии. **Официально
   рекомендованный обход** для Gen4 (fang, neato-brainslug). ← практический минимум.
2. **Brain-transplant (RPi4 + ESP32 + ROS2)** по образцу `neat-pi` — полный локальный контроль, переиспользуя
   механику/лидар/моторы/батарею, штатная электроника выбрасывается. Усилия очень высокие (недели), риск
   высокий, зрелость проекта ранняя. Единственный путь к «настоящему» локальному роботу. ← цель, если нужен максимум.
3. Chip-off/ISP-дамп eMMC — только разведка (без обхода secure boot не даёт управления). Гипотеза.
4. Обход secure boot i.MX (HAB/DCD-CSF/SDP) — экстремально, лаборатория уровня NCC/QuarksLab, fused ли HAB
   на D9 неизвестно. Гипотеза, низкие шансы.
5. U-Boot / single-user / сброс пароля по UART — два Gen4-экспериментатора сообщают о подписанной
   залоченной консоли. Практически тупик.
6. Перепривязка D9 → живое облако MyKobold/Vorwerk — **тупик**: прошивку Kobold на Gen4 не залить (secure
   boot), серверная валидация не признаёт Neato «genuine Kobold» (опыт даже с D7→VR300 провалился).
7. Fake-cloud / MITM neatocloud.com — **тупик** (TLS pinning, отказ от RFC1918; доказано).
8. Cloud-библиотеки pybotvac/pyneato — **мертвы** для Neato после отключения neatocloud.com.

## Рекомендация

- «Включать/выключать уборку локально с минимумом усилий» → **вектор 1** (ESP32 на кнопку).
- «Настоящий локальный робот с картами/навигацией» → **вектор 2** (brain-transplant, серьёзный проект).
- Штатные мозги D9 (Linux/i.MX, signed, secure boot) community на 2026 считает недоступными: ни одного
  публично зафиксированного взлома именно Gen4 нет.

## Ключевые источники

- Jiska Classen, PhD thesis, TU Darmstadt 2020, DOI 10.25534/tuprints-00011422 (глава II.4 — про пред. поколение).
- Ullrich & Classen, «Vacuum Cleaning Security», DEF CON 27 (2019); WOOT'19 «Vacuums in the Cloud».
  CVE-2018-20785 (secure boot, пропатчен 4.4.0-72), CVE-2018-19441 (энтропия ключа).
- fang: https://github.com/vacuula/fang (Gen4 unsupported, «wire esp32 to the button»).
- neato-brainslug: https://github.com/Philip2809/neato-brainslug (Gen4 «not yet», ESP32 на кнопку).
- neat-pi: https://github.com/dweng0/neat-pi (brain-transplant D10, ROS2).
- pybotvac: https://github.com/stianaske/pybotvac (Vorwerk client_id MyKobold, cloud-only).
- Neato→Kobold опыт: https://github.com/RobertSundling/neato-botvac/discussions/15 (D7→VR300, провал регистрации).
- CVE i.MX HAB: CVE-2017-7932, CVE-2022-45163 (NCC Group).
- Лидар под ROS: Hackaday project 171893, mica-angeli/pidar.
