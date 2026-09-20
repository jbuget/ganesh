import { SignInPage } from "@/components/organisms/SignInPage";

/**
 * The screen that asks who you are.
 *
 * Which door it shows is decided here, on the server: the browser has no say
 * in it, and cannot ask for the other one.
 */
export default function SignIn() {
  return <SignInPage entra={process.env.AUTH_ENTRA !== "false"} />;
}
