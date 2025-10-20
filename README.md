# auto_OTP

## Guide: Creating the Android OTP Forwarder App
    This guide outlines the necessary steps and code logic to create a simple Android app that reads OTPs from incoming SMS messages and forwards them to the otp_server.py running on your computer.

1. Project Setup
    Create a new Android Studio project.
    Choose "Empty Activity" and use Kotlin or Java.

3. Permissions
    You must request permission to read SMS messages. Add the following to your AndroidManifest.xml file, inside the <manifest> tag:

<uses-permission android:name="android.permission.RECEIVE_SMS" />
<uses-permission android:name="android.permission.INTERNET" />


3. Create a BroadcastReceiver
   The core of the app is a BroadcastReceiver that listens for incoming SMS messages.

    Create a new Kotlin class, for example, SmsReceiver.kt.
    
    import android.content.BroadcastReceiver
    import android.content.Context
    import android.content.Intent
    import android.provider.Telephony
    import android.util.Log
    import okhttp3.*
    import okhttp3.MediaType.Companion.toMediaTypeOrNull
    import okhttp3.RequestBody.Companion.toRequestBody
    import org.json.JSONObject
    import java.io.IOException
    import java.util.regex.Pattern
    
    class SmsReceiver : BroadcastReceiver() {
    
        // IMPORTANT: Replace with your computer's IP address on the local network.
        // Do not use 127.0.0.1 or localhost as the phone won't be able to reach it.
        private val serverUrl = "[http://192.168.1.10:8088/store_otp](http://192.168.1.10:8088/store_otp)"
        private val client = OkHttpClient()
    
        override fun onReceive(context: Context, intent: Intent) {
            if (intent.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
                val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
                for (smsMessage in messages) {
                    val messageBody = smsMessage.messageBody
                    Log.d("SmsReceiver", "Message received: $messageBody")
                    
                    // Attempt to extract the OTP from the message body
                    extractOtp(messageBody)?.let { otp ->
                        Log.d("SmsReceiver", "OTP Found: $otp")
                        sendOtpToServer(otp)
                    }
                }
            }
        }
    
        // A simple regex to find a 6-digit number.
        // You should tailor this regex to match the format of the OTPs you receive.
        private fun extractOtp(message: String): String? {
            val pattern = Pattern.compile("(\\d{6})") // Looks for 6 consecutive digits
            val matcher = pattern.matcher(message)
            return if (matcher.find()) {
                matcher.group(0)
            } else {
                null
            }
        }
    
        private fun sendOtpToServer(otp: String) {
            val json = JSONObject()
            json.put("otp", otp)
            val requestBody = json.toString()
                .toRequestBody("application/json; charset=utf-8".toMediaTypeOrNull())
    
            val request = Request.Builder()
                .url(serverUrl)
                .post(requestBody)
                .build()
    
            client.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    Log.e("SmsReceiver", "Failed to send OTP to server", e)
                }
    
                override fun onResponse(call: Call, response: Response) {
                    if (response.isSuccessful) {
                        Log.d("SmsReceiver", "Successfully sent OTP to server.")
                    } else {
                        Log.e("SmsReceiver", "Server responded with error: ${response.code}")
                    }
                    response.close() // Close the response body
                }
            })
        }
    }


4. Register the Receiver
    Register the BroadcastReceiver in your AndroidManifest.xml inside the <application> tag. This allows it to receive system broadcasts for SMS messages.

    <receiver
        android:name=".SmsReceiver"
        android:enabled="true"
        android:exported="true">
        <intent-filter>
            <action android:name="android.provider.Telephony.SMS_RECEIVED" />
        </intent-filter>
    </receiver>


5. Add Dependencies
    You'll need an HTTP client library to send the OTP to your server. OkHttp is a great choice. Add it to your app-level build.gradle file:

    dependencies {
        // ... other dependencies
        implementation("com.squareup.okhttp3:okhttp:4.9.3")
    }


6. Runtime Permissions
    For Android 6.0 (API 23) and higher, you must request the RECEIVE_SMS permission from the user at runtime. In your MainActivity.kt, you can add code to request this permission when the app starts.

## How to Use This Setup

1. Find your Computer's IP Address: On your testing machine (running Burp), find its local network IP address (e.g., 192.168.1.10).

2. Update Android App: Change the serverUrl variable in SmsReceiver.kt to your computer's IP address.

3. Run the Android App: Install and run the app on your physical Android device. Grant it SMS permissions when prompted.

4. Run the OTP Server: On your computer, run the Flask server: python otp_server.py.

5. Load the Burp Extension: In Burp Suite, go to the Extender tab, click Add, choose 'Python' as the extension type, and select the otp_autofill.py file.

6. Configure the Extension: Go to the new "OTP AutoFill" tab in Burp. Set the "Target Host" to the domain of the app you're testing (e.g., api.yourapp.com) and ensure the "OTP Parameter Name" matches what the application expects (e.g., otp, code, pin).

7. Test: Trigger an OTP request in the mobile app. The SMS should arrive on your phone, the Android app will forward it to your server, and the Burp extension will automatically fetch and inject it into the intercepted request.
