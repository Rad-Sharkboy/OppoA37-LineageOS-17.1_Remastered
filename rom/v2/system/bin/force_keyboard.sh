#!/system/bin/sh
sleep 5
while true; do
    IME_ID=$(ime list -a -s | grep "com.simplemobiletools.keyboard" | tr -d '\r')
    if [ -n "$IME_ID" ]; then
        settings put secure enabled_input_methods "$IME_ID"
        settings put secure default_input_method "$IME_ID"
        ime enable "$IME_ID"
        ime set "$IME_ID"
        break
    fi
    sleep 2
done

sleep 15

# Play Store Background Junk & Ads
pm disable 'com.android.vending/com.google.android.finsky.flushlogs.FlushLogsReceiver$FlushLogsService'
pm disable 'com.android.vending/com.google.android.finsky.hygiene.DailyHygiene$DailyHygieneService'
pm disable 'com.android.vending/com.google.android.finsky.services.AdIdListener'
pm disable 'com.android.vending/com.google.android.gms.ads.AdActivity'

# GMS Ads, Analytics & Telemetry Uploaders
pm disable 'com.google.android.gms/com.google.android.gms.ads.AdRequestBrokerService'
pm disable 'com.google.android.gms/com.google.android.gms.ads.identifier.service.AdvertisingIdService'
pm disable 'com.google.android.gms/com.google.android.gms.analytics.AnalyticsService'
pm disable 'com.google.android.gms/com.google.android.gms.clearcut.service.ClearcutLoggerService'
pm disable 'com.google.android.gms/com.google.android.gms.clearcut.uploader.UploaderService'
pm disable 'com.google.android.gms/com.google.android.gms.stats.PlatformStatsCollectorService'
pm disable 'com.google.android.gms/com.google.android.gms.usagereporting.service.UsageReportingService'

# GMS Wearables & Fitness + Android Auto
pm disable 'com.google.android.gms/com.google.android.gms.wearable.service.WearableService'
pm disable 'com.google.android.gms/com.google.android.gms.wearable.service.WearableControlService'
pm disable 'com.google.android.gms/com.google.android.gms.fitness.sync.FitnessSyncAdapterService'
pm disable 'com.google.android.gms/com.google.android.gms.fitness.wearables.WearableSyncService'
pm disable 'com.google.android.gms/com.google.android.gms.car.CarService'

# Background Media/App Scanners (Maps & YouTube)
pm disable 'com.google.android.apps.maps/com.google.android.apps.gmm.offline.update.StartAutoUpdatesCheckingReceiver'
pm disable 'com.google.android.apps.maps/com.google.android.apps.gmm.navigation.service.detection.StartDetectionReceiver'
pm disable 'com.google.android.youtube/com.google.android.libraries.youtube.mdx.background.MdxBackgroundScanBootReceiver'