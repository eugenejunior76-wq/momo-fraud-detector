package com.atuedu.momofrauddetector;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.os.Build;
import androidx.core.app.NotificationCompat;
import com.atuedu.momofrauddetector.models.PredictResponse;

public class NotificationHelper {

    private static final String CHANNEL_FRAUD = "fraud_alerts";
    private static final String CHANNEL_SAFE  = "safe_messages";

    public static void show(Context ctx, String message, PredictResponse result) {
        NotificationManager manager =
            (NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE);

        // Create notification channels (required for Android 8+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            manager.createNotificationChannel(new NotificationChannel(
                CHANNEL_FRAUD, "Fraud Alerts", NotificationManager.IMPORTANCE_HIGH
            ));
            manager.createNotificationChannel(new NotificationChannel(
                CHANNEL_SAFE, "Safe Messages", NotificationManager.IMPORTANCE_LOW
            ));
        }

        // Trim message for display
        String preview = message.length() > 80
            ? message.substring(0, 80) + "…"
            : message;

        NotificationCompat.Builder builder;

        if (result.is_fraud) {
            // Red fraud warning notification
            builder = new NotificationCompat.Builder(ctx, CHANNEL_FRAUD)
                .setSmallIcon(android.R.drawable.ic_dialog_alert)
                .setContentTitle("⚠️ Fraud SMS Detected")
                .setContentText(preview)
                .setStyle(new NotificationCompat.BigTextStyle()
                    .bigText("This message appears to be a MoMo scam.\n\n\"" + preview + "\""))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setColor(0xFFC62828)
                .setAutoCancel(true);
        } else {
            // Green safe notification
            builder = new NotificationCompat.Builder(ctx, CHANNEL_SAFE)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle("✅ Legitimate SMS")
                .setContentText(preview)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .setColor(0xFF2E7D32)
                .setAutoCancel(true);
        }

        // Add confidence score to notification if available
        if (result.confidence != null) {
            builder.setSubText("Confidence: " + result.confidence + "%");
        }

        manager.notify((int) System.currentTimeMillis(), builder.build());
    }
}