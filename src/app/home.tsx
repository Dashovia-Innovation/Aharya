import { router } from 'expo-router';

import { AuthScreen, PrimaryButton } from '@/components/auth';

// ponytail: placeholder until the report upload screen exists
export default function Home() {
  return (
    <AuthScreen title="Home" subtitle="Report upload and AI summary coming next.">
      <PrimaryButton title="Log out" onPress={() => router.replace('/sign-in')} />
    </AuthScreen>
  );
}
