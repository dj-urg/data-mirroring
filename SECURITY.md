# Securing the Data Mirror Application
Welcome to the security section of our Data Mirror application. Here, we walk you through the various steps we've taken to ensure your data is handled with the utmost care. This includes an overview of:

- **Coding Practices:** Adopting robust and secure development principles to safeguard the integrity of the application.
- **Hosting Practices:** Ensuring a secure and reliable hosting environment for seamless operation.
- **Routing Practices:** Implementing safe routing mechanisms to protect data during its journey.
- **GDPR Compliance:** Aligning with data protection regulations to respect your privacy and uphold transparency.

The security of our website has been tested using the [ImmuniWeb Security Test](https://www.immuniweb.com/websec).

Explore each area to see how security remains at the heart of our development process.

## Privacy-Oriented Coding

This application is designed with privacy and security as top priorities, adhering to best practices to ensure data protection and secure operations. Key measures include:

### Framework and Design
- **Flask Framework:** The application is built on Flask, a lightweight and secure Python framework known for its simplicity and robustness.
- **Modular Architecture:** The codebase follows a modular design, promoting separation of concerns. This approach enhances maintainability and minimizes the risk of vulnerabilities by isolating critical components.

### Security Features
- **Content Security Policy (CSP):** A dynamic CSP is applied to every response, utilizing nonces to prevent the execution of unauthorized scripts and restrict trusted sources for content (e.g., styles, fonts, and images). This significantly reduces the risk of cross-site scripting (XSS) attacks.
- **HTTPS Enforcement:** HTTP traffic is automatically redirected to HTTPS in production environments to ensure encrypted communications. This is achieved through strict request handling and checks for secure origins.
- **Strict Security Headers:** Key headers like `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy` are included to defend against common web vulnerabilities such as clickjacking, MIME-type sniffing, and insecure resource sharing.
- **Session Management:** Secure and HTTP-only cookies are used with SameSite policies to protect session data. Session lifetime is limited, and additional measures like CSRF protection ensure safe interactions with the server.
- **Temporary File Management:** Temporary files are automatically cleaned up after each session and periodically to prevent accidental data retention and reduce the risk of unauthorized access.

### Additional Safeguards
- **Rate Limiting:** To mitigate the risk of denial-of-service (DoS) attacks, API endpoints are protected with rate limits, ensuring fair usage and service availability.
- **Authentication and Access Control:** Only authenticated users can access sensitive routes. Authentication is handled securely, and input validation is enforced to prevent injection attacks.
- **Cross-Origin Resource Sharing (CORS):** CORS is configured to allow only trusted origins, preventing unauthorized domains from interacting with the application.
- **Logging and Monitoring:** Comprehensive logging is in place to monitor application behavior and track potential security events while avoiding logging sensitive user data.
- **File Sanitization:** Uploaded files are thoroughly validated and securely stored in temporary directories. Strict checks are implemented to prevent directory traversal attacks or unauthorized file access.

### Privacy Commitment
This application is designed to prioritize user privacy:
- **No Data Retention:** User data is processed only during the session and deleted after the session ends, ensuring no residual data is stored on the server.
- **Scoped Permissions:** The application uses a principle of least privilege, granting only the necessary permissions for specific operations.

By combining these features, this application delivers a secure and privacy-conscious user experience while meeting modern security standards.

In addition, we have enabled various security features within GitHub such as **Dependabot alerts**, which flags vulnerability in the code base and **Code scanning alerts**, which automatically detect common vulnerability and coding errors. 

## Hosting on a Secure Third Party
The app is hosted on **Heroku**, a platform known for its security and scalability. Hosting measures include:
- **HTTPS Support:** Ensures secure data transmission between users and the server.
- **Environment Variable Management:** Secrets, such as API keys and database credentials, are stored securely using environment variables.
- **Isolation:** The app runs in isolated containers, minimizing the risk of cross-application vulnerabilities.
- **Data Localisation:** The app runs on Heroku's EU-based servers.

Local development uses Docker to replicate production-like environments, reducing discrepancies and security risks during deployment.

## Routed
Domain routing ensures all traffic is handled securely and efficiently.
- The app is accessible via the primary domain **data-mirror-72f6ffc87917.herokuapp.com**.
- **HTTPS Redirection:** Any HTTP requests are automatically redirected to HTTPS to enforce encryption.
- **Domain Whitelisting:** Only allowed hosts can be accessed, preventing spoofing and unauthorized redirection attempts.
- **Response Validation:** Routes are secured to prevent injection and ensure only intended resources are served.

## GDPR Compliance
The app adheres to **GDPR regulations**, emphasizing user data protection and privacy. Key features include:
- **No Data Retention:** The app processes user-uploaded data temporarily during a session. Once the session ends, all data is deleted immediately.
- **Secure Data Handling:** Data is encrypted in transit using HTTPS.
- **Transparency:** Clear communication with users about data handling policies.
- **User Control:** User data can be uploaded and processed, and is directly removed without any long-term storage.

By implementing these practices, the app ensures compliance with GDPR’s principles, including data minimization, transparency, and security, while fostering user trust.
