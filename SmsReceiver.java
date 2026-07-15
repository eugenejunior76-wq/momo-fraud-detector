package com.atuedu.momofrauddetector;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.telephony.SmsMessage;

public class SmsReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        if (!intent.getAction().equals("android.provider.Telephony.SMS_RECEIVED")) return;

        Bundle bundle = intent.getExtras();
        if (bundle == null) return;

        // Extract SMS body from the intent
        Object[] pdus = (Object[]) bundle.get("pdus");
        if (pdus == null) return;

        String format = bundle.getString("format");
        StringBuilder fullMessage = new StringBuilder();

        for (Object pdu : pdus) {
            SmsMessage sms = SmsMessage.createFromPdu((byte[]) pdu, format);
            fullMessage.append(sms.getMessageBody());
        }

        String messageText = fullMessage.toString().trim();
        if (messageText.isEmpty()) return;

        // Send to API in background thread
        Intent serviceIntent = new Intent(context, AnalysisService.class);
        serviceIntent.putExtra("message", messageText);
        context.startService(serviceIntent);
    }
}