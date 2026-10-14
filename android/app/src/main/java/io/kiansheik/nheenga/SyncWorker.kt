package io.kiansheik.nheenga

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.*
import java.util.concurrent.TimeUnit

class SyncWorker(context: Context, parameters: WorkerParameters) : Worker(context, parameters) {
    private val library = Library.get(context)
    private val started = System.currentTimeMillis()
    private var lastProgress = 0L
    override fun doWork(): Result {
        if (library.paused()) return Result.success()
        return try {
            if (inputData.getBoolean("foreground", false)) {
                setForegroundAsync(notification("Preparando downloads", 0, 0)).get()
            }
            library.sync({ isStopped || System.currentTimeMillis() - started > 7 * 60_000 }) { name, done, total ->
                if (System.currentTimeMillis() - lastProgress > 500) {
                    lastProgress = System.currentTimeMillis()
                    val text = "$name: ${done / 1_000_000} / ${total / 1_000_000} MB"
                    library.status(text)
                    setProgressAsync(workDataOf("text" to text, "done" to done, "total" to total))
                    if (inputData.getBoolean("foreground", false)) {
                        val manager = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                        manager.notify(NOTIFICATION, notification(text, done, total).notification)
                    }
                }
            }
            Result.success()
        } catch (error: Exception) {
            library.status(error.message ?: "Falha no download; sua biblioteca foi preservada")
            if (library.paused() || isStopped) Result.success() else Result.retry()
        }
    }
    private fun notification(text: String, done: Long, total: Long): ForegroundInfo {
        val manager = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= 26) manager.createNotificationChannel(
            NotificationChannel(CHANNEL, "Downloads da biblioteca", NotificationManager.IMPORTANCE_LOW))
        val pause = PendingIntent.getBroadcast(applicationContext, 0, Intent(applicationContext, PauseDownloads::class.java), PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val open = PendingIntent.getActivity(applicationContext, 1, Intent(applicationContext, MainActivity::class.java), PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val notification = NotificationCompat.Builder(applicationContext, CHANNEL)
            .setSmallIcon(android.R.drawable.stat_sys_download).setContentTitle("Nhe'enga")
            .setContentText(text).setContentIntent(open).setOnlyAlertOnce(true).setOngoing(true)
            .setProgress(1000, if (total > 0) (done * 1000 / total).toInt() else 0, total == 0L)
            .addAction(android.R.drawable.ic_media_pause, "Pausar", pause).build()
        return if (Build.VERSION.SDK_INT >= 29) ForegroundInfo(NOTIFICATION, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
            else ForegroundInfo(NOTIFICATION, notification)
    }
    companion object {
        private const val CHANNEL = "library-downloads"
        private const val NOTIFICATION = 17
        private const val NOW = "nhe-library-sync"
        private const val PERIODIC = "nhe-library-periodic"
        private fun constraints(context: Context): Constraints = Constraints.Builder()
            .setRequiredNetworkType(if (Library.get(context).preferences.getBoolean("metered", false)) NetworkType.CONNECTED else NetworkType.UNMETERED)
            .setRequiresStorageNotLow(true).build()
        fun schedule(context: Context, foreground: Boolean = false, now: Boolean = true) {
            val library = Library.get(context)
            if (library.paused()) return
            val manager = WorkManager.getInstance(context)
            manager.enqueueUniquePeriodicWork(PERIODIC, ExistingPeriodicWorkPolicy.UPDATE,
                PeriodicWorkRequestBuilder<SyncWorker>(12, TimeUnit.HOURS).setConstraints(constraints(context)).build())
            if (now) manager.enqueueUniqueWork(NOW, ExistingWorkPolicy.KEEP,
                OneTimeWorkRequestBuilder<SyncWorker>().setConstraints(constraints(context))
                    .setInputData(workDataOf("foreground" to foreground))
                    .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS).build())
        }
        fun pause(context: Context) {
            Library.get(context).pause()
            WorkManager.getInstance(context).cancelUniqueWork(NOW)
            WorkManager.getInstance(context).cancelUniqueWork(PERIODIC)
        }
        fun restart(context: Context) {
            val manager = WorkManager.getInstance(context)
            manager.cancelUniqueWork(NOW).result.get()
            schedule(context, foreground = true)
        }
    }
}
class PauseDownloads : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) { SyncWorker.pause(context) }
}
