package io.kiansheik.nheenga

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.Message
import android.view.Gravity
import android.view.View
import android.webkit.*
import android.widget.*
import androidx.webkit.WebViewAssetLoader
import android.net.Uri
import java.util.concurrent.Executors

/** Native chrome only. All dictionary/search/citation UI remains the website. */
class MainActivity : Activity() {
    private lateinit var library: Library
    private val executor = Executors.newSingleThreadExecutor()
    private val handler = Handler(Looper.getMainLooper())
    private var screen = 0
    private var web: WebView? = null
    private var statusView: TextView? = null
    private val local = "https://appassets.androidplatform.net"
    private val basePath = "/nhe-enga/"
    private val poll = object : Runnable {
        override fun run() { statusView?.text = library.status(); handler.postDelayed(this, 1000) }
    }
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        library = Library.get(this)
        if (library.coreReady()) showWebsite() else settings()
        SyncWorker.schedule(this)
    }
    override fun onResume() { super.onResume(); handler.post(poll); if (System.currentTimeMillis() - library.preferences.getLong("lastCheck", 0) > 6 * 3600000) SyncWorker.schedule(this) }
    override fun onPause() { handler.removeCallbacks(poll); super.onPause() }
    override fun onDestroy() { handler.removeCallbacks(poll); web?.destroy(); executor.shutdown(); super.onDestroy() }
    private fun column(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        val pad = (12 * resources.displayMetrics.density).toInt(); setPadding(pad, pad, pad, pad)
        // targetSdk 35 edge-to-edge: keep native controls clear of system bars.
        setOnApplyWindowInsetsListener { view, insets ->
            view.setPadding(pad + insets.systemWindowInsetLeft, pad + insets.systemWindowInsetTop,
                pad + insets.systemWindowInsetRight, pad + insets.systemWindowInsetBottom); insets
        }
    }
    private fun LinearLayout.text(value: String): TextView = TextView(this@MainActivity).also { it.text = value; it.setPadding(0, 12, 0, 12); addView(it) }
    private fun LinearLayout.button(value: String, action: () -> Unit) = Button(this@MainActivity).also {
        it.text = value; it.setOnClickListener { action() }; addView(it)
    }
    private fun async(action: () -> Unit) {
        executor.execute { try { action() } catch (e: Exception) {
            library.status(e.message ?: "Não foi possível concluir a operação")
            runOnUiThread { Toast.makeText(this, library.status(), Toast.LENGTH_LONG).show() }
        } }
    }
    private fun settings() {
        val revision = ++screen
        web?.destroy(); web = null
        val layout = column(); setContentView(ScrollView(this).apply { addView(layout) })
        layout.text("Nhe'enga sem internet").textSize = 24f
        layout.text("Escolha seus downloads. Os dicionários são pequenos; as imagens das fontes são opcionais. Depois do primeiro download, o aplicativo abre a cópia local.")
        statusView = layout.text(library.status())
        val content = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }; layout.addView(content)
        layout.button("Consultar opções / atualizações") { async { val c = library.refreshCatalog(); runOnUiThread { if (revision == screen) populate(content, c) } } }
        layout.button("Verificar atualização do aplicativo") {
            async {
                val updates = AppUpdates(); val release = updates.latest()
                runOnUiThread {
                    if (isFinishing || isDestroyed || revision != screen) return@runOnUiThread
                    if (release == null || release.versionCode <= BuildConfig.VERSION_CODE) {
                        AlertDialog.Builder(this).setMessage("Seu aplicativo está atualizado (${BuildConfig.VERSION_NAME}). Os dicionários são atualizados separadamente.")
                            .setPositiveButton("OK", null).show()
                    } else {
                        AlertDialog.Builder(this).setTitle("Nhe'enga ${release.versionName}")
                            .setMessage("Baixar atualização (${"%.1f".format(release.bytes / 1_000_000.0)} MB)?\n\nO APK é assinado e distribuído gratuitamente fora da Play Store. O Android pode pedir que você permita instalar apps desta fonte nas configurações do navegador. Autorize apenas se confiar na origem. O Android confirma a instalação; seus downloads são preservados ao atualizar, sem desinstalar.")
                            .setNegativeButton("Cancelar", null).setPositiveButton("Baixar") { _, _ ->
                                try { startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(updates.downloadUrl))) }
                                catch (_: Exception) { Toast.makeText(this, "Não há navegador para baixar o aplicativo", Toast.LENGTH_LONG).show() }
                            }.show()
                    }
                }
            }
        }
        layout.button("Pausar downloads") { SyncWorker.pause(this) }
        layout.button("Abrir dicionários / aplicar versão baixada") {
            if (library.coreReady()) showWebsite() else Toast.makeText(this, "Baixe os dicionários primeiro", Toast.LENGTH_SHORT).show()
        }
        layout.button("Restaurar versão anterior") { SyncWorker.pause(this); async { library.rollback(); runOnUiThread { showWebsite() } } }
        layout.text("Atualizações são verificadas ao abrir o app e periodicamente quando o Android permite. Desinstalar ou limpar os dados remove a biblioteca. Nenhuma imagem é apagada automaticamente para liberar espaço.")
        val existing = library.cachedCatalog()
        populate(content, existing)
        if (existing == null) async { val c = library.refreshCatalog(); runOnUiThread { if (revision == screen) populate(content, c) } }
    }
    private fun populate(layout: LinearLayout, catalog: Catalog?) {
        layout.removeAllViews()
        val s = library.state(); val selected = s.getJSONArray("selected")
        val selectedIds = (0 until selected.length()).map { selected.getString(it) }.toSet()
        val boxes = mutableMapOf<String, CheckBox>()
        for (p in catalog?.packs.orEmpty()) {
            val row = CheckBox(this).apply {
                text = "${p.title} — ${"%.1f".format(p.bytes / 1_000_000.0)} MB"
                isChecked = p.id in selectedIds || p.id == "core"; isEnabled = p.id != "core"
            }
            boxes[p.id] = row; layout.addView(row)
        }
        for ((id, title) in library.removablePacks()) {
            val label = catalog?.packs?.find { it.id == id }?.title ?: title
            layout.button("Remover $label") {
                AlertDialog.Builder(this).setMessage("Remover os arquivos baixados deste pacote?")
                    .setNegativeButton("Cancelar", null).setPositiveButton("Remover") { _, _ ->
                        SyncWorker.pause(this); async { library.remove(id); runOnUiThread { populate(layout, catalog) } }
                    }.show()
            }
        }
        if (catalog == null) return
        val all = CheckBox(this).apply { text = "Todas as fontes, incluindo novas coleções"; isChecked = s.optBoolean("allSources") }; layout.addView(all)
        val metered = CheckBox(this).apply { text = "Permitir dados móveis (downloads e atualizações)"; isChecked = library.preferences.getBoolean("metered", false) }; layout.addView(metered)
        val estimate = layout.text("")
        fun total() {
            val bytes = catalog.packs.filter { boxes[it.id]?.isChecked == true || (all.isChecked && it.kind == "source") }.sumOf { it.bytes }
            estimate.text = "Seleção completa: ${"%.1f".format(bytes / 1_000_000.0)} MB. Arquivos iguais não serão baixados novamente."
        }
        boxes.values.forEach { it.setOnCheckedChangeListener { _, _ -> total() } }; all.setOnCheckedChangeListener { _, _ -> total() }; total()
        layout.button("Salvar / baixar seleção") {
            if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 9)
            }
            val ids = boxes.filterValues { it.isChecked }.keys.toSet()
            val wantsAll = all.isChecked; val wantsMetered = metered.isChecked
            async {
                library.configure(ids, wantsAll, wantsMetered)
                SyncWorker.restart(this)
                library.status(if (wantsMetered) "Download solicitado" else "Download solicitado; aguardando conexão não tarifada (Wi-Fi)")
            }
        }
        val storage = layout.text("Calculando armazenamento…")
        async { val used = library.usedBytes(); runOnUiThread { storage.text = "Biblioteca no celular: ${"%.1f".format(used / 1_000_000.0)} MB" } }
    }
    private fun navigate(uri: Uri): Boolean {
        if (uri.scheme in setOf("https", "http") &&
            (uri.host == "appassets.androidplatform.net" || uri.host == "kiansheik.io") && uri.path?.startsWith(basePath) == true) {
            if (uri.path == basePath + "offline/" || uri.path == basePath + "offline/index.html") { settings(); return true }
            if (uri.host != "appassets.androidplatform.net") {
                web?.loadUrl(local + uri.encodedPath + (uri.encodedQuery?.let { "?$it" } ?: "") + (uri.encodedFragment?.let { "#$it" } ?: "")); return true
            }
            return false
        }
        // Never load third-party pages into the privileged/local WebView.
        if (uri.scheme in setOf("https", "http", "mailto")) {
            try { startActivity(Intent(Intent.ACTION_VIEW, uri)) } catch (_: Exception) { Toast.makeText(this, "Não há aplicativo para abrir este link", Toast.LENGTH_SHORT).show() }
        }
        return true
    }
    private fun unavailable(mime: String = "text/plain") = WebResourceResponse(mime, "utf-8", 404, "Not Downloaded",
        mapOf("Cache-Control" to "no-store"), "Este arquivo ainda não foi baixado. Abra Downloads quando tiver internet.".byteInputStream())
    private fun showWebsite() {
        if (!library.coreReady()) { settings(); return }
        val revision = ++screen
        val layout = FrameLayout(this).apply {
            setOnApplyWindowInsetsListener { view, insets ->
                view.setPadding(insets.systemWindowInsetLeft, insets.systemWindowInsetTop,
                    insets.systemWindowInsetRight, insets.systemWindowInsetBottom); insets
            }
        }
        setContentView(layout)
        statusView = null
        async {
            val session = library.session()
            runOnUiThread {
                if (isFinishing || isDestroyed || revision != screen) return@runOnUiThread
                val view = WebView(this); web = view
                val loader = WebViewAssetLoader.Builder().addPathHandler(basePath) { relative ->
                    try {
                        var path = relative
                        if (path.isEmpty() || path.endsWith('/')) path += "index.html"
                        else if (!path.substringAfterLast('/').contains('.')) path += "/index.html"
                        val result = library.open(path, session)
                        if (result == null) unavailable() else {
                            val (f, file) = result
                            WebResourceResponse(f.mime, if (f.mime.startsWith("text/") || f.mime == "application/javascript") "utf-8" else null,
                                200, "OK", mapOf("Cache-Control" to "no-store", "X-Content-Type-Options" to "nosniff",
                                    "Content-Security-Policy" to "default-src 'self' data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'self'"), file.inputStream())
                        }
                    } catch (_: Exception) { unavailable() }
                }.build()
                view.settings.apply {
                    javaScriptEnabled = true; domStorageEnabled = true
                    allowFileAccess = false; allowContentAccess = false
                    mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
                    setSupportMultipleWindows(true)
                    cacheMode = WebSettings.LOAD_NO_CACHE
                }
                CookieManager.getInstance().setAcceptThirdPartyCookies(view, false)
                WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG)
                view.webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(v: WebView, request: WebResourceRequest) = navigate(request.url)
                    @Deprecated("Required by old WebViews")
                    override fun shouldOverrideUrlLoading(v: WebView, url: String) = navigate(Uri.parse(url))
                    override fun shouldInterceptRequest(v: WebView, request: WebResourceRequest): WebResourceResponse {
                        val u = request.url
                        if (request.method != "GET") return unavailable()
                        if (u.scheme == "https" && u.host == "appassets.androidplatform.net") return loader.shouldInterceptRequest(u) ?: unavailable()
                        if (u.scheme == "https" && u.host == "kiansheik.io" && u.path?.startsWith(basePath) == true)
                            return loader.shouldInterceptRequest(Uri.parse(local + u.encodedPath)) ?: unavailable()
                        return unavailable() // Includes analytics/CDNs, not just top-level navigation.
                    }
                    override fun onRenderProcessGone(v: WebView, detail: RenderProcessGoneDetail): Boolean {
                        v.destroy(); web = null; settings(); library.status("O visualizador foi reiniciado; os downloads foram preservados"); return true
                    }
                }
                view.webChromeClient = object : WebChromeClient() {
                    override fun onCreateWindow(v: WebView, dialog: Boolean, userGesture: Boolean, result: Message): Boolean {
                        if (!userGesture) return false
                        val popup = WebView(this@MainActivity)
                        popup.webViewClient = object : WebViewClient() {
                            override fun shouldOverrideUrlLoading(v: WebView, request: WebResourceRequest): Boolean {
                                val handled = navigate(request.url)
                                if (!handled) web?.loadUrl(request.url.toString())
                                popup.destroy(); return true
                            }
                        }
                        (result.obj as WebView.WebViewTransport).webView = popup; result.sendToTarget(); return true
                    }
                }
                layout.addView(view, FrameLayout.LayoutParams(-1, -1))
                val density = resources.displayMetrics.density
                val settingsButton = ImageButton(this).apply {
                    setImageResource(R.drawable.ic_settings)
                    contentDescription = "Configurações e downloads"
                    val padding = (12 * density).toInt(); setPadding(padding, padding, padding, padding)
                    val background = android.util.TypedValue()
                    theme.resolveAttribute(android.R.attr.selectableItemBackgroundBorderless, background, true)
                    setBackgroundResource(background.resourceId)
                    if (Build.VERSION.SDK_INT >= 26) tooltipText = contentDescription
                    setOnClickListener { settings() }
                }
                layout.addView(settingsButton, FrameLayout.LayoutParams((48 * density).toInt(), (48 * density).toInt(), Gravity.TOP or Gravity.END).apply {
                    topMargin = (4 * density).toInt(); marginEnd = (4 * density).toInt()
                })
                view.loadUrl(local + basePath)
            }
        }
    }
    @Deprecated("Use platform back navigation")
    override fun onBackPressed() { if (web?.canGoBack() == true) web?.goBack() else if (web == null && library.coreReady()) showWebsite() else super.onBackPressed() }
}
