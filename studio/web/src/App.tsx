/**
 * Application shell.
 *
 * The navigation and page frame every later screen sits inside: the dashboard, the
 * world page, the generation review and the history list.
 */

import { useStyletron } from "baseui";
import {
  HeaderNavigation,
  ALIGN,
  StyledNavigationItem,
  StyledNavigationList,
} from "baseui/header-navigation";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { HeadingSmall, LabelMedium, ParagraphMedium } from "baseui/typography";

import { PhaseNotice, ServiceStatus } from "./components/ServiceStatus";
import type { ThemeName } from "./theme";

export interface AppProps {
  themeName: ThemeName;
  onToggleTheme: () => void;
}

export function App({ themeName, onToggleTheme }: AppProps): React.JSX.Element {
  const [css, theme] = useStyletron();

  return (
    <div className={css({ minHeight: "100vh", backgroundColor: theme.colors.backgroundPrimary })}>
      <HeaderNavigation>
        <StyledNavigationList $align={ALIGN.left}>
          <StyledNavigationItem>
            <LabelMedium>Shirtfaced Studio</LabelMedium>
          </StyledNavigationItem>
        </StyledNavigationList>
        <StyledNavigationList $align={ALIGN.center} />
        <StyledNavigationList $align={ALIGN.right}>
          <StyledNavigationItem>
            <Button size={SIZE.compact} kind={BUTTON_KIND.tertiary} onClick={onToggleTheme}>
              {themeName === "light" ? "Dark theme" : "Light theme"}
            </Button>
          </StyledNavigationItem>
        </StyledNavigationList>
      </HeaderNavigation>

      <main
        className={css({
          maxWidth: "960px",
          marginRight: "auto",
          marginLeft: "auto",
          paddingTop: theme.sizing.scale900,
          paddingRight: theme.sizing.scale800,
          paddingBottom: theme.sizing.scale900,
          paddingLeft: theme.sizing.scale800,
        })}
      >
        <HeadingSmall marginTop={0}>Dashboard</HeadingSmall>
        <ParagraphMedium color={theme.colors.contentSecondary}>
          A private production tool for building coherent Shirtfaced photographic worlds.
        </ParagraphMedium>

        <div
          className={css({
            display: "grid",
            gap: theme.sizing.scale700,
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            marginTop: theme.sizing.scale800,
          })}
        >
          <ServiceStatus />
          <PhaseNotice />
        </div>
      </main>
    </div>
  );
}
