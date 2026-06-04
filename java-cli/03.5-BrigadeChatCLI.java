///usr/bin/env jbang "$0" "$@" ; exit $?
//JAVA 17+
//DEPS dev.tamboui:tamboui-toolkit:0.3.0
//DEPS dev.tamboui:tamboui-panama-backend:0.3.0
//DEPS dev.tamboui:tamboui-markdown:0.3.0
//DEPS com.google.code.gson:gson:2.10.1

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import dev.tamboui.style.Color;
import dev.tamboui.toolkit.app.ToolkitRunner;
import dev.tamboui.markdown.MarkdownView;
import dev.tamboui.toolkit.element.Element;
import dev.tamboui.toolkit.event.EventResult;
import dev.tamboui.tui.event.Event;
import dev.tamboui.tui.event.KeyEvent;
import dev.tamboui.widgets.input.TextInputState;
import dev.tamboui.widgets.spinner.SpinnerStyle;
import static dev.tamboui.toolkit.Toolkit.*;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

public class BrigadeChatCLI {

    static final String API_BASE = "http://localhost:8000";

    record Message(String role, String content) {}

    // ── état ───────────────────────────────────────────────────────────────
    private String sessionId = null;
    private final List<Message> history = new ArrayList<>();
    private String statusMessage = "";
    private boolean loading = false;
    private String errorMessage = null;
    private int windowOffset = 0;       // 0 = dernier échange, 1 = avant-dernier, etc.
    private int brigadeScrollOffset = 0; // lignes skippées dans la réponse Brigade courante
    private final TextInputState inputState = new TextInputState("");
    private ToolkitRunner runner;

    private final HttpClient http = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(5))
            .build();

    // ── rendu ──────────────────────────────────────────────────────────────

    public Element render() {
        return column(
            renderHeader(),
            renderHistory(),
            renderFooter()
        );
    }

    private Element renderHeader() {
        String sessionLabel = sessionId != null
                ? "  session : " + sessionId.substring(0, 8) + "…"
                : "";
        return panel("Cooking Brigade",
            row(
                text("La brigade est prête.").italic(),
                text(sessionLabel).dim()
            )
        ).borderColor(Color.YELLOW);
    }

    // Retourne les 2 messages (1 échange) correspondant à la fenêtre courante
    private List<Message> visibleMessages() {
        int total = history.size();
        if (total == 0) return List.of();
        int end   = Math.max(0, total - windowOffset * 2);
        int start = Math.max(0, end - 2);
        return history.subList(start, end);
    }

    private boolean canScrollUp()   { return history.size() > (windowOffset + 1) * 2; }
    private boolean canScrollDown() { return windowOffset > 0; }

    private Element renderHistory() {
        if (errorMessage != null) {
            return panel("Erreur", text(errorMessage).red()).borderColor(Color.RED);
        }
        if (!statusMessage.isEmpty()) {
            return panel("", text(statusMessage).dim().italic());
        }
        if (history.isEmpty()) {
            return panel("",
                text("Aucun message pour l'instant…").dim().italic()
            );
        }
        var items = new ArrayList<Element>();
        if (canScrollUp()) {
            items.add(text("  ↑ PgUp — échange précédent").dim());
        }
        for (Message msg : visibleMessages()) {
            if ("user".equals(msg.role())) {
                items.add(panel("Vous", text(msg.content())).borderColor(Color.GREEN));
            } else {
                var mdView = MarkdownView.builder()
                        .source(msg.content())
                        .scroll(brigadeScrollOffset)
                        .build();
                String scrollHint = brigadeScrollOffset > 0 ? " [ligne " + brigadeScrollOffset + "]" : "";
                items.add(
                    panel("Brigade  ↑↓ pour défiler" + scrollHint,
                        widget(mdView)
                    ).borderColor(Color.BLUE).fill()
                );
            }
        }
        if (canScrollDown()) {
            items.add(text("  ↓ PgDn — échange suivant").dim());
        }
        return column(items.toArray(Element[]::new));
    }

    private Element renderFooter() {
        if (loading) {
            return panel("",
                row(spinner(SpinnerStyle.DOTS, "La brigade travaille…").cyan())
            );
        }
        return column(
            panel("",
                row(
                    text("Vous").bold().green(),
                    text(" › ").dim(),
                    textInput(inputState).fill()
                )
            ),
            text("  ↑↓ défiler la réponse · PgUp/PgDn échange précédent/suivant · /reset · /quit").dim()
        );
    }

    // ── clavier ────────────────────────────────────────────────────────────

    private EventResult handleKey(KeyEvent event) {
        if (loading) return EventResult.HANDLED;
        if (event.isQuit()) {
            runner.quit();
            return EventResult.HANDLED;
        }
        if (event.isPageUp()) {
            if (canScrollUp()) { windowOffset++; brigadeScrollOffset = 0; }
            return EventResult.HANDLED;
        }
        if (event.isPageDown()) {
            if (canScrollDown()) { windowOffset--; brigadeScrollOffset = 0; }
            return EventResult.HANDLED;
        }
        if (event.isDown()) {
            brigadeScrollOffset++;
            return EventResult.HANDLED;
        }
        if (event.isUp()) {
            brigadeScrollOffset = Math.max(0, brigadeScrollOffset - 1);
            return EventResult.HANDLED;
        }
        if (event.isConfirm()) {
            String input = inputState.text().trim();
            inputState.setText("");
            if (!input.isEmpty()) processCommand(input);
            return EventResult.HANDLED;
        }
        if (handleTextInputKey(inputState, event)) {
            return EventResult.HANDLED;
        }
        return EventResult.UNHANDLED;
    }

    private void processCommand(String input) {
        statusMessage = "";
        errorMessage = null;
        switch (input) {
            case "/quit"    -> runner.quit();
            case "/reset"   -> { sessionId = null; history.clear(); statusMessage = "Session réinitialisée."; }
            case "/history" -> statusMessage = history.isEmpty() ? "Aucun historique." : "";
            default         -> sendMessage(input);
        }
    }

    // ── HTTP ───────────────────────────────────────────────────────────────

    private void sendMessage(String message) {
        loading = true;
        errorMessage = null;

        JsonObject body = new JsonObject();
        body.addProperty("message", message);
        if (sessionId != null) body.addProperty("session_id", sessionId);

        var request = HttpRequest.newBuilder()
                .uri(URI.create(API_BASE + "/chat"))
                .header("Content-Type", "application/json")
                .timeout(Duration.ofSeconds(300))
                .POST(HttpRequest.BodyPublishers.ofString(body.toString()))
                .build();

        http.sendAsync(request, HttpResponse.BodyHandlers.ofString())
            .thenAccept(resp -> runner.runOnRenderThread(() -> {
                loading = false;
                if (resp.statusCode() == 200) {
                    var json = JsonParser.parseString(resp.body()).getAsJsonObject();
                    sessionId = json.get("session_id").getAsString();
                    history.add(new Message("user", message));
                    history.add(new Message("assistant", json.get("response").getAsString()));
                    windowOffset = 0;        // revenir au dernier échange
                    brigadeScrollOffset = 0; // rembobiner la réponse
                } else {
                    errorMessage = "Erreur API " + resp.statusCode() + " — " + resp.body();
                }
            }))
            .exceptionally(ex -> {
                runner.runOnRenderThread(() -> {
                    loading = false;
                    errorMessage = "Erreur réseau : " + ex.getCause().getMessage();
                });
                return null;
            });
    }

    // ── health check (avant ouverture du TUI) ─────────────────────────────

    private static void checkApiOrExit() {
        try {
            var req = HttpRequest.newBuilder()
                    .uri(URI.create(API_BASE + "/health"))
                    .timeout(Duration.ofSeconds(5))
                    .GET().build();
            var resp = HttpClient.newBuilder()
                    .version(HttpClient.Version.HTTP_1_1)
                    .build()
                    .send(req, HttpResponse.BodyHandlers.ofString());
            if (resp.statusCode() != 200)
                throw new RuntimeException("statut " + resp.statusCode());
        } catch (Exception e) {
            System.err.println("L'API n'est pas disponible sur " + API_BASE);
            System.err.println("Démarrez-la avec : uv run python 06-conversation.py");
            System.exit(1);
        }
    }

    // ── lancement ─────────────────────────────────────────────────────────

    public static void main(String[] args) throws Exception {
        checkApiOrExit();
        BrigadeChatCLI app = new BrigadeChatCLI();
        app.runner = ToolkitRunner.create();
        app.runner.eventRouter().addGlobalHandler((Event event) -> {
            if (event instanceof KeyEvent key) return app.handleKey(key);
            return EventResult.UNHANDLED;
        });
        app.runner.run(app::render);
    }
}
