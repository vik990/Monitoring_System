/* JavaScript for resident profiles page */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function sendManualAlert(profileId) {
    if (!confirm('Send a usage alert to this profile? This will include current month usage summary.')) return;

    const csrftoken = getCookie('csrftoken');
    fetch(`/alerts/send-manual/${profileId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Accept': 'application/json',
        },
    })
    .then(function(response) {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            alert(data.message);
            // Optionally refresh to show new alert badge
            window.location.reload();
        } else {
            alert('Failed to send alert: ' + data.message);
        }
    })
    .catch(function(error) {
        alert('Error sending alert. Please check your email configuration and server logs.');
    });
}

function sendTestEmail(profileId) {
    if (!confirm('Send a test email to this profile to validate SMTP settings?')) return;
    const csrftoken = getCookie('csrftoken');

    fetch(`/residents/${profileId}/send-test-email/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Accept': 'application/json',
        },
    })
    .then(function(response) {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(function(data) {
        if (data.success) {
            alert(data.message);
        } else {
            alert('Test email failed: ' + data.message);
        }
    })
    .catch(function(error) {
        alert('Error sending test email. See server logs.');
    });
}