<?php
// send_email.php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle CORS preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode([
        'success' => false,
        'message' => 'Method not allowed. Please use POST.'
    ]);
    exit();
}

// Start output buffering to catch any errors
ob_start();

try {
    // Collect and sanitize form data
    $name = isset($_POST['name']) ? trim(htmlspecialchars($_POST['name'])) : '';
    $email = isset($_POST['email']) ? trim(htmlspecialchars($_POST['email'])) : '';
    $phone = isset($_POST['phone']) ? trim(htmlspecialchars($_POST['phone'])) : '';
    $subject = isset($_POST['subject']) ? trim(htmlspecialchars($_POST['subject'])) : '';
    $message = isset($_POST['message']) ? trim(htmlspecialchars($_POST['message'])) : '';
    
    // Get client IP and user agent for logging
    $ip_address = $_SERVER['REMOTE_ADDR'] ?? 'Unknown';
    $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? 'Unknown';
    $timestamp = date('Y-m-d H:i:s');
    
    // Validate required fields
    $errors = [];
    
    if (empty($name)) {
        $errors[] = 'Name is required.';
    } elseif (strlen($name) < 2) {
        $errors[] = 'Name must be at least 2 characters.';
    }
    
    if (empty($email)) {
        $errors[] = 'Email address is required.';
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $errors[] = 'Please enter a valid email address.';
    }
    
    if (empty($subject)) {
        $errors[] = 'Subject is required.';
    }
    
    if (empty($message)) {
        $errors[] = 'Message is required.';
    } elseif (strlen($message) < 10) {
        $errors[] = 'Message must be at least 10 characters.';
    } elseif (strlen($message) > 2000) {
        $errors[] = 'Message must not exceed 2000 characters.';
    }
    
    // Validate phone if provided
    if (!empty($phone) && !preg_match('/^[\+]?[0-9\s\-\(\)]{10,}$/', $phone)) {
        $errors[] = 'Please enter a valid phone number.';
    }
    
    // If there are validation errors
    if (!empty($errors)) {
        echo json_encode([
            'success' => false,
            'message' => implode(' ', $errors)
        ]);
        exit();
    }
    
    // Email configuration
    $to_email = "elijahokware@gmail.com"; // Your receiving email
    $to_name = "WellMed Support Team";
    
    // Subject with prefix
    $email_subject = "📧 WellMed Contact: $subject";
    
    // Create HTML email body
    $email_body = '
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>New Contact Form Submission</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
            }
            .email-wrapper {
                max-width: 600px;
                margin: 0 auto;
            }
            .email-container {
                background: white;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
            }
            .email-header {
                background: linear-gradient(135deg, #6c63ff 0%, #36d1dc 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }
            .email-header h1 {
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }
            .email-header p {
                margin: 10px 0 0;
                opacity: 0.9;
                font-size: 16px;
            }
            .email-body {
                padding: 40px;
            }
            .field-group {
                margin-bottom: 25px;
                padding-bottom: 25px;
                border-bottom: 1px solid #f0f0f0;
            }
            .field-group:last-child {
                border-bottom: none;
                margin-bottom: 0;
                padding-bottom: 0;
            }
            .field-label {
                font-size: 14px;
                font-weight: 600;
                color: #6c63ff;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
                display: block;
            }
            .field-value {
                font-size: 16px;
                color: #555;
                line-height: 1.6;
            }
            .field-value.message {
                background: #f8f9ff;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #6c63ff;
                white-space: pre-wrap;
            }
            .highlight-box {
                background: linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%);
                border-left: 4px solid #ff6584;
                padding: 20px;
                margin: 30px 0;
                border-radius: 10px;
            }
            .highlight-box h3 {
                color: #d32f2f;
                margin-top: 0;
            }
            .email-footer {
                background: #f8f9ff;
                padding: 25px 40px;
                text-align: center;
                font-size: 14px;
                color: #888;
                border-top: 1px solid #eee;
            }
            .email-footer a {
                color: #6c63ff;
                text-decoration: none;
                font-weight: 500;
            }
            .metadata {
                font-size: 12px;
                color: #999;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }
        </style>
    </head>
    <body>
        <div class="email-wrapper">
            <div class="email-container">
                <div class="email-header">
                    <h1>📬 New Contact Form Submission</h1>
                    <p>WellMed Mental Health Support System</p>
                </div>
                
                <div class="email-body">
                    <div class="field-group">
                        <span class="field-label">Name</span>
                        <div class="field-value">' . $name . '</div>
                    </div>
                    
                    <div class="field-group">
                        <span class="field-label">Email Address</span>
                        <div class="field-value">
                            <a href="mailto:' . $email . '" style="color: #6c63ff; text-decoration: none;">' . $email . '</a>
                        </div>
                    </div>
                    
                    <div class="field-group">
                        <span class="field-label">Phone Number</span>
                        <div class="field-value">' . (!empty($phone) ? $phone : 'Not provided') . '</div>
                    </div>
                    
                    <div class="field-group">
                        <span class="field-label">Subject</span>
                        <div class="field-value" style="color: #6c63ff; font-weight: 600;">' . $subject . '</div>
                    </div>
                    
                    <div class="field-group">
                        <span class="field-label">Message</span>
                        <div class="field-value message">' . nl2br($message) . '</div>
                    </div>
                    
                    <div class="field-group">
                        <span class="field-label">Submitted On</span>
                        <div class="field-value">' . date('F j, Y \a\t g:i a') . '</div>
                    </div>
                    
                    ' . ($subject === 'Emergency Support' ? '
                    <div class="highlight-box">
                        <h3>⚠️ EMERGENCY ALERT</h3>
                        <p>This message has been flagged as an <strong>EMERGENCY SUPPORT</strong> request. Please respond urgently.</p>
                        <p><strong>Recommended action:</strong> Call the user immediately at ' . (!empty($phone) ? $phone : 'email provided') . '</p>
                    </div>
                    ' : '') . '
                    
                    <div class="metadata">
                        Submission ID: ' . uniqid('wellmed_') . '<br>
                        IP Address: ' . $ip_address . '<br>
                        User Agent: ' . substr($user_agent, 0, 100) . '
                    </div>
                </div>
                
                <div class="email-footer">
                    <p>This message was sent from the WellMed contact form.<br>
                    <a href="mailto:' . $email . '">Reply to ' . $email . '</a> | 
                    <a href="tel:+254759226354">Call Support: +254 759 226354</a></p>
                </div>
            </div>
        </div>
    </body>
    </html>';
    
    // Email headers
    $headers = "From: WellMed Contact Form <noreply@wellmed.com>\r\n";
    $headers .= "Reply-To: " . $name . " <" . $email . ">\r\n";
    $headers .= "MIME-Version: 1.0\r\n";
    $headers .= "Content-Type: text/html; charset=UTF-8\r\n";
    $headers .= "X-Mailer: PHP/" . phpversion() . "\r\n";
    $headers .= "X-Priority: " . ($subject === 'Emergency Support' ? '1 (Highest)' : '3 (Normal)') . "\r\n";
    
    // Additional parameters for mail()
    $additional_params = "-f noreply@wellmed.com";
    
    // Attempt to send email
    $mail_sent = mail($to_email, $email_subject, $email_body, $headers, $additional_params);
    
    if ($mail_sent) {
        // Log successful submission
        $log_entry = sprintf(
            "[%s] SUCCESS | Name: %s | Email: %s | Phone: %s | Subject: %s | IP: %s | User-Agent: %s\n",
            $timestamp,
            $name,
            $email,
            $phone ?: 'N/A',
            $subject,
            $ip_address,
            substr($user_agent, 0, 100)
        );
        
        // Save to log file
        $log_file = __DIR__ . '/contact_log.txt';
        file_put_contents($log_file, $log_entry, FILE_APPEND);
        
        // Save to CSV for easier analysis
        $csv_file = __DIR__ . '/contact_submissions.csv';
        $csv_header = "Timestamp,Name,Email,Phone,Subject,Message,IP,UserAgent,Status\n";
        
        if (!file_exists($csv_file)) {
            file_put_contents($csv_file, $csv_header);
        }
        
        $csv_data = sprintf(
            '"%s","%s","%s","%s","%s","%s","%s","%s","Success"' . "\n",
            $timestamp,
            addslashes($name),
            addslashes($email),
            addslashes($phone),
            addslashes($subject),
            addslashes(substr($message, 0, 500)),
            $ip_address,
            addslashes(substr($user_agent, 0, 200))
        );
        
        file_put_contents($csv_file, $csv_data, FILE_APPEND);
        
        // Send auto-reply to user
        $this->sendAutoReply($email, $name, $subject);
        
        echo json_encode([
            'success' => true,
            'message' => '✅ Thank you! Your message has been sent successfully. We will respond within 24 hours.'
        ]);
        
    } else {
        // Log failed attempt
        $log_entry = sprintf(
            "[%s] FAILED | Name: %s | Email: %s | Phone: %s | Subject: %s | IP: %s | Error: Mail function failed\n",
            $timestamp,
            $name,
            $email,
            $phone ?: 'N/A',
            $subject,
            $ip_address
        );
        
        $log_file = __DIR__ . '/contact_errors.txt';
        file_put_contents($log_file, $log_entry, FILE_APPEND);
        
        echo json_encode([
            'success' => false,
            'message' => '❌ Sorry, we encountered an error while sending your message. Please try again or contact us directly at elijahokware@gmail.com'
        ]);
    }
    
} catch (Exception $e) {
    // Catch any unexpected errors
    error_log("Contact form error: " . $e->getMessage());
    
    echo json_encode([
        'success' => false,
        'message' => '❌ An unexpected error occurred. Please try again later.'
    ]);
    
} finally {
    // Clean output buffer
    ob_end_flush();
}

/**
 * Send auto-reply to the user
 */
private function sendAutoReply($to_email, $to_name, $subject) {
    $auto_subject = "Thank you for contacting WellMed";
    
    $auto_body = '
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #6c63ff, #36d1dc); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { padding: 30px; background: #f9f9ff; border-radius: 0 0 10px 10px; }
            .footer { text-align: center; padding: 20px; color: #666; font-size: 14px; border-top: 1px solid #eee; margin-top: 30px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Thank You for Contacting WellMed</h2>
            </div>
            <div class="content">
                <p>Hi ' . $to_name . ',</p>
                <p>Thank you for reaching out to us regarding: <strong>' . $subject . '</strong></p>
                <p>We have received your message and our team will review it shortly. We aim to respond within 24 hours.</p>
                
                <div style="background: #fff; padding: 20px; border-radius: 8px; border-left: 4px solid #6c63ff; margin: 20px 0;">
                    <p><strong>What happens next?</strong></p>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Our team will review your message</li>
                        <li>We\'ll contact you via email or phone</li>
                        <li>We\'ll provide the support or information you need</li>
                    </ul>
                </div>
                
                <p><strong>For immediate assistance:</strong></p>
                <p>📞 Call: <a href="tel:+254759226354" style="color: #6c63ff; text-decoration: none;">+254 759 226354</a><br>
                📱 WhatsApp: <a href="https://wa.me/254759226354" style="color: #6c63ff; text-decoration: none;">+254 759 226354</a></p>
                
                <p><strong>Emergency contacts:</strong><br>
                🚨 Nairobi Women\'s Hospital: 0800 720 720<br>
                🚨 Emergency Services: 999 or 112</p>
                
                <p>Best regards,<br>
                <strong>The WellMed Team</strong></p>
            </div>
            <div class="footer">
                <p>This is an automated response. Please do not reply to this email.</p>
                <p>&copy; ' . date('Y') . ' WellMed Mental Health Support System</p>
            </div>
        </div>
    </body>
    </html>';
    
    $auto_headers = "From: WellMed <noreply@wellmed.com>\r\n";
    $auto_headers .= "MIME-Version: 1.0\r\n";
    $auto_headers .= "Content-Type: text/html; charset=UTF-8\r\n";
    
    @mail($to_email, $auto_subject, $auto_body, $auto_headers, "-f noreply@wellmed.com");
}
?>
