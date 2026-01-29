<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $name = htmlspecialchars($_POST['name']);
    $email = htmlspecialchars($_POST['email']);
    $phone = htmlspecialchars($_POST['phone'] ?? 'Not provided');
    $service = htmlspecialchars($_POST['service'] ?? 'General Inquiry');
    $message = htmlspecialchars($_POST['message']);
    
    $to = "elijahokware@gmail.com";
    $subject = "New Contact Form: $name - $service";
    
    $body = "
    Name: $name
    Email: $email
    Phone: $phone
    Service: $service
    
    Message:
    $message
    
    ---
    Sent from Elmed Wellmind Website
    Time: " . date('Y-m-d H:i:s');
    
    $headers = "From: website@elmedwellmind.com\r\n";
    $headers .= "Reply-To: $email\r\n";
    
    if (mail($to, $subject, $body, $headers)) {
        echo json_encode(['success' => true, 'message' => 'Email sent successfully!']);
    } else {
        echo json_encode(['success' => false, 'message' => 'Failed to send email.']);
    }
}
?>