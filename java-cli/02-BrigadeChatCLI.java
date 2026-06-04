///usr/bin/env jbang "$0" "$@" ; exit $?
//JAVA 17+
//DEPS dev.tamboui:tamboui-toolkit:0.3.0
//DEPS dev.tamboui:tamboui-panama-backend:0.3.0

import dev.tamboui.style.Color;
import dev.tamboui.toolkit.app.ToolkitRunner;
import dev.tamboui.toolkit.element.Element;
import dev.tamboui.toolkit.event.EventResult;
import dev.tamboui.tui.event.Event;
import dev.tamboui.tui.event.KeyEvent;
import dev.tamboui.widgets.input.TextInputState;
import static dev.tamboui.toolkit.Toolkit.*;

import java.util.ArrayList;
import java.util.List;

public class BrigadeChatCLI {

    record Message(String role, String content) {}

    // ── état ───────────────────────────────────────────────────────────────
    private final List<Message> history = new ArrayList<>();
    private String statusMessage = "";
    private final TextInputState inputState = new TextInputState("");
    private ToolkitRunner runner;

    // ── rendu ──────────────────────────────────────────────────────────────

    public Element render() {
        return column(
            renderHeader(),
            renderHistory(),
            renderFooter()
        );
    }

    private Element renderHeader() {
        return panel("Cooking Brigade",
            text("Décrivez votre repas idéal et la brigade créera un menu sur mesure.").italic()
        ).borderColor(Color.YELLOW);
    }

    private Element renderHistory() {
        if (!statusMessage.isEmpty()) {
            return panel("Historique", text(statusMessage).dim().italic());
        }
        if (history.isEmpty()) {
            return panel("Historique", text("Aucun message pour l'instant…").dim().italic());
        }
        var items = new ArrayList<Element>();
        for (Message msg : history) {
            if ("user".equals(msg.role())) {
                items.add(panel("Vous", text(msg.content())).borderColor(Color.GREEN));
            } else {
                items.add(panel("Brigade", text(msg.content())).borderColor(Color.BLUE));
            }
        }
        return column(items.toArray(Element[]::new));
    }

    private Element renderFooter() {
        return column(
            panel("",
                row(
                    text("Vous").bold().green(),
                    text(" › ").dim(),
                    textInput(inputState).fill()
                )
            ),
            text("  /reset · /history · /quit").dim()
        );
    }

    // ── clavier ────────────────────────────────────────────────────────────

    private EventResult handleKey(KeyEvent event) {
        if (event.isQuit()) {
            runner.quit();
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
        switch (input) {
            case "/quit"    -> runner.quit();
            case "/reset"   -> { history.clear(); statusMessage = "Session réinitialisée."; }
            case "/history" -> statusMessage = history.isEmpty() ? "Aucun historique." : "";
            default         -> sendMessage(input);
        }
    }

    private void sendMessage(String message) {
        // sera implémenté à l'étape 3
        history.add(new Message("user", message));
        history.add(new Message("assistant", "[HTTP non encore connecté]"));
    }

    // ── lancement ─────────────────────────────────────────────────────────

    public static void main(String[] args) throws Exception {
        BrigadeChatCLI app = new BrigadeChatCLI();
        app.runner = ToolkitRunner.create();
        app.runner.eventRouter().addGlobalHandler((Event event) -> {
            if (event instanceof KeyEvent key) return app.handleKey(key);
            return EventResult.UNHANDLED;
        });
        app.runner.run(app::render);
    }
}
