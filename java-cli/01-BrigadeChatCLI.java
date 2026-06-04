///usr/bin/env jbang "$0" "$@" ; exit $?
//JAVA 17+
//DEPS dev.tamboui:tamboui-toolkit:0.3.0
//DEPS dev.tamboui:tamboui-panama-backend:0.3.0

import dev.tamboui.style.Color;
import dev.tamboui.toolkit.app.ToolkitRunner;
import dev.tamboui.toolkit.element.Element;
import static dev.tamboui.toolkit.Toolkit.*;

public class BrigadeChatCLI {

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
        return panel("Historique",
            text("Aucun message pour l'instant…").dim().italic()
        );
    }

    private Element renderFooter() {
        return column(
            panel("",
                row(
                    text("Vous").bold().green(),
                    text(" › ").dim(),
                    text("commencez à taper…").dim()
                )
            ),
            text("  /reset · /history · /quit").dim()
        );
    }

    public static void main(String[] args) throws Exception {
        BrigadeChatCLI app = new BrigadeChatCLI();
        ToolkitRunner runner = ToolkitRunner.create();
        runner.run(app::render);
    }
}
