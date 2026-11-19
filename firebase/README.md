# Firebase для каталога

Каталог хранит отметки «У меня есть» в Cloud Firestore по пути `users/{uid}/catalogOwnership/{isbn}`. Конфигурация веб-приложения находится в сгенерированном `index.html` и не является секретом; доступ ограничивается правилами Firestore.

В Firebase Console:

1. В **Authentication → Sign-in method** включите **Email/Password**.
2. В **Authentication → Settings → Authorized domains** добавьте `b10nicle.github.io` и `localhost` для локальной проверки.
3. В **Firestore Database** создайте базу в production mode.
4. Вкладка **Rules**: вставьте содержимое `firestore.rules` и нажмите **Publish**.

При первом входе сохранённые локальные отметки объединяются с облачными. Снятие отметки удаляет только документ текущего пользователя.
