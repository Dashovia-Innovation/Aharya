import { Stack } from 'expo-router';

import { useAuthTheme } from '@/components/auth';

export default function AuthLayout() {
  const { c } = useAuthTheme();
  return (
    <Stack
      screenOptions={{
        title: '',
        headerTransparent: true,
        headerTintColor: c.title,
        headerBackTitle: 'Back',
        headerShadowVisible: false,
        contentStyle: { backgroundColor: c.bg },
      }}>
      <Stack.Screen name="index" options={{ headerShown: false }} />
    </Stack>
  );
}
