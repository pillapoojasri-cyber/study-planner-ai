if (Notification.permission !== "granted") {
    Notification.requestPermission();
}

function checkReminders() {

    let now = new Date();

    let currentDate = now.toISOString().split("T")[0];

    let currentTime =
        String(now.getHours()).padStart(2, "0")
        + ":"
        + String(now.getMinutes()).padStart(2, "0");

    tasks.forEach(function(task) {

        if (
            task.due_date === currentDate &&
            task.due_time === currentTime &&
            task.completed === 0
        ) {

            new Notification(
                "📚 Study Planner",
                {
                    body: "Time to study: " + task.name
                }
            );
        }

    });

}

setInterval(checkReminders, 60000);