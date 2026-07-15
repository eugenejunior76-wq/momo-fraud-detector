package com.atuedu.momofrauddetector;

import android.app.IntentService;
import android.content.Intent;
import com.google.gson.Gson;
import com.atuedu.momofrauddetector.models.PredictRequest;
import com.atuedu.momofrauddetector.models.PredictResponse;
import okhttp3.*;
import java.io.IOException;

public class AnalysisService extends IntentService {

    // ← Replace with your Render URL
    private static final String API_URL = "https://momo-fraud-detector.onrender.com";

    private final OkHttpClient client = new OkHttpClient();
    private final Gson gson = new Gson();

    public AnalysisService() {
        super("AnalysisService");
    }

    @Override
    protected void onHandleIntent(Intent intent) {
        if (intent == null) return;

        String message = intent.getStringExtra("message");
        if (message == null || message.isEmpty()) return;

        // Build JSON request
        String json = gson.toJson(new PredictRequest(message));
        RequestBody body = RequestBody.create(
            json, MediaType.get("application/json; charset=utf-8")
        );

        Request request = new Request.Builder()
            .url(API_URL)
            .post(body)
            .build();

        try {
            Response response = client.newCall(request).execute();
            if (response.isSuccessful() && response.body() != null) {
                String responseBody = response.body().string();
                PredictResponse result = gson.fromJson(responseBody, PredictResponse.class);

                // Show notification with result
                NotificationHelper.show(this, message, result);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
