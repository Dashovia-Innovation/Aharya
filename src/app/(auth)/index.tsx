import { router } from 'expo-router';
import { SymbolView } from 'expo-symbols';
import { StatusBar } from 'expo-status-bar';
import { useRef, useState, type ReactNode } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const TEAL = '#0F8B8D';
const DEEP = '#0B4F55';
const WHITE = '#FFFFFF';
const BLACK = '#000000';
const AMBER = '#8A3B00';
// Teal darkened for small text on white (brand Teal is ~4.1:1, under AA)
const TEAL_TEXT = '#0B6E70';

const SLIDES: { title: string; card?: ReactNode }[] = [
  { title: 'Your health\nmade simple' },
  {
    title: 'Your reports,\nexplained in\nplain words.',
    card: (
      <PhoneMockup>
        <ReportCard />
      </PhoneMockup>
    ),
  },
  {
    title: 'Meals planned\naround your\nresults.',
    card: (
      <PhoneMockup>
        <DietCard />
      </PhoneMockup>
    ),
  },
];

// Intro is always brand teal (like a splash), regardless of light/dark mode
export default function Welcome() {
  // measured, not window width: correct inside any container and on web static render
  const [{ width, height }, setSize] = useState({ width: 0, height: 0 });
  const scroller = useRef<ScrollView>(null);
  const [page, setPage] = useState(0);
  const last = page === SLIDES.length - 1;

  const goTo = (i: number) => {
    scroller.current?.scrollTo({ x: i * width, animated: true });
    setPage(i);
  };
  const onScrollEnd = (e: NativeSyntheticEvent<NativeScrollEvent>) =>
    setPage(Math.round(e.nativeEvent.contentOffset.x / width));

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="light" />
      {/* soft background shapes, like the reference */}
      <View style={[styles.blob, { top: -80, right: -120 }]} />
      <View style={[styles.blob, { bottom: 80, left: -160 }]} />

      <View style={styles.topBar}>
        <Text style={styles.brand}>aharya</Text>
        {!last && (
          <Pressable
            onPress={() => router.push('/sign-up')}
            accessibilityRole="button"
            style={styles.skip}>
            <Text style={styles.skipText}>Skip</Text>
          </Pressable>
        )}
      </View>

      <ScrollView
        ref={scroller}
        style={styles.flex}
        onLayout={(e) => setSize(e.nativeEvent.layout)}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={onScrollEnd}>
        {SLIDES.map((s, i) => (
          <View
            key={i}
            style={[styles.slide, { width, height }, !s.card && styles.slideBottom]}
            accessibilityElementsHidden={i !== page}
            importantForAccessibility={i === page ? 'auto' : 'no-hide-descendants'}>
            <Text style={styles.title} accessibilityRole="header">
              {s.title}
            </Text>
            {s.card}
          </View>
        ))}
      </ScrollView>

      <View style={styles.bottomBar}>
        <View style={styles.dots} accessibilityLabel={`Slide ${page + 1} of ${SLIDES.length}`}>
          {SLIDES.map((_, i) => (
            <View key={i} style={[styles.dot, i === page && styles.dotOn]} />
          ))}
        </View>
        {last ? (
          <Pressable
            onPress={() => router.push('/sign-up')}
            accessibilityRole="button"
            style={({ pressed }) => [styles.cta, pressed && styles.pressed]}>
            <Text style={styles.ctaText}>Get started</Text>
            <Chevrons />
          </Pressable>
        ) : (
          <Pressable
            onPress={() => goTo(page + 1)}
            accessibilityRole="button"
            accessibilityLabel="Next"
            style={({ pressed }) => [styles.next, pressed && styles.pressed]}>
            <Chevrons />
          </Pressable>
        )}
      </View>
      <Pressable
        onPress={() => router.push('/sign-in')}
        accessibilityRole="link"
        style={styles.signIn}>
        <Text style={styles.signInText}>
          Already have an account? <Text style={styles.signInBold}>Sign in</Text>
        </Text>
      </Pressable>
    </SafeAreaView>
  );
}

function Chevrons() {
  return (
    <SymbolView
      name={{
        ios: 'chevron.forward.2',
        android: 'keyboard_double_arrow_right',
        web: 'keyboard_double_arrow_right',
      }}
      size={22}
      tintColor={WHITE}
      accessible={false}
    />
  );
}

/** Drawn iPhone frame; it is cropped by the slide's bottom edge, like an app-store shot. */
function PhoneMockup({ children }: { children: ReactNode }) {
  return (
    <View style={styles.phone}>
      <View style={styles.phoneScreen}>
        <View style={styles.statusBar}>
          <Text style={styles.time}>9:41</Text>
          <View style={styles.island} />
          <View style={styles.battery}>
            <View style={styles.batteryFill} />
          </View>
        </View>
        {children}
      </View>
    </View>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <View style={styles.card}>
      <View style={styles.cardHead}>
        <Text style={styles.cardTitle}>{title}</Text>
        <Text style={styles.example}>Example</Text>
      </View>
      {children}
    </View>
  );
}

// Sample markers: normal range [lo, hi] drawn on a wider [min, max] scale
const MARKERS = [
  { name: 'Haemoglobin', value: 13.8, unit: 'g/dL', lo: 12, hi: 16, min: 8, max: 20 },
  { name: 'Vitamin D', value: 18, unit: 'ng/mL', lo: 30, hi: 100, min: 0, max: 120 },
  { name: 'Fasting glucose', value: 92, unit: 'mg/dL', lo: 70, hi: 100, min: 50, max: 150 },
];

const pct = (v: number, min: number, max: number) =>
  `${Math.min(100, Math.max(0, ((v - min) / (max - min)) * 100))}%` as const;

function ReportCard() {
  const status = (m: (typeof MARKERS)[number]) =>
    m.value < m.lo ? 'Low' : m.value > m.hi ? 'High' : 'Normal';
  const flagged = MARKERS.filter((m) => status(m) !== 'Normal').length;
  return (
    <Card title="Blood report summary">
      <View style={styles.summary}>
        <Text style={[styles.pill, styles.pillOk]}>{MARKERS.length - flagged} Normal</Text>
        <Text style={[styles.pill, styles.pillLow]}>{flagged} Needs attention</Text>
      </View>
      {MARKERS.map((m) => {
        const s = status(m);
        const ok = s === 'Normal';
        return (
          <View
            key={m.name}
            style={styles.marker}
            accessible
            accessibilityLabel={`${m.name} ${m.value} ${m.unit}, ${s}. Normal range ${m.lo} to ${m.hi}.`}>
            <View style={styles.markerHead}>
              <Text style={styles.rowName}>{m.name}</Text>
              <Text style={[styles.status, ok ? styles.statusOk : styles.statusLow]}>
                {ok ? '●' : '▲'} {s}
              </Text>
            </View>
            <Text style={styles.rowValue}>
              {m.value} <Text style={styles.unit}>{m.unit}</Text>
            </Text>
            <View style={styles.track}>
              <View
                style={[
                  styles.normalZone,
                  {
                    left: pct(m.lo, m.min, m.max),
                    right: `${100 - parseFloat(pct(m.hi, m.min, m.max))}%`,
                  },
                ]}
              />
              <View
                style={[
                  styles.thumb,
                  { left: pct(m.value, m.min, m.max) },
                  ok ? styles.thumbOk : styles.thumbLow,
                ]}
              />
            </View>
          </View>
        );
      })}
      <View style={styles.insight}>
        <SymbolView
          name={{ ios: 'sparkles', android: 'auto_awesome', web: 'auto_awesome' }}
          size={16}
          tintColor={DEEP}
          accessible={false}
        />
        <Text style={styles.insightText}>
          Vitamin D is low. Try morning sunlight, eggs and fortified milk.
        </Text>
      </View>
    </Card>
  );
}

const MEALS = [
  {
    meal: 'Breakfast',
    time: '8:00 AM',
    food: 'Ragi dosa with sprouts',
    kcal: 380,
    tag: 'High iron',
    icon: { ios: 'sunrise.fill', android: 'wb_twilight', web: 'wb_twilight' },
  },
  {
    meal: 'Lunch',
    time: '1:30 PM',
    food: 'Dal, brown rice, palak',
    kcal: 520,
    tag: 'High fibre',
    icon: { ios: 'sun.max.fill', android: 'light_mode', web: 'light_mode' },
  },
  {
    meal: 'Dinner',
    time: '8:00 PM',
    food: 'Grilled paneer and salad',
    kcal: 450,
    tag: 'Vitamin D',
    icon: { ios: 'moon.fill', android: 'dark_mode', web: 'dark_mode' },
  },
] as const;

function DietCard() {
  const total = MEALS.reduce((sum, m) => sum + m.kcal, 0);
  return (
    <Card title="Today's diet plan">
      <View style={styles.summary}>
        <Text style={[styles.pill, styles.pillOk]}>{total} kcal</Text>
        <Text style={[styles.pill, styles.pillLow]}>Vitamin D focus</Text>
      </View>
      {MEALS.map((m) => (
        <View
          key={m.meal}
          style={styles.meal}
          accessible
          accessibilityLabel={`${m.meal} at ${m.time}: ${m.food}, ${m.kcal} calories, ${m.tag}.`}>
          <View style={styles.mealIcon}>
            <SymbolView name={m.icon} size={18} tintColor={TEAL_TEXT} accessible={false} />
          </View>
          <View style={styles.flex}>
            <View style={styles.markerHead}>
              <Text style={styles.rowName}>
                {m.meal} · {m.time}
              </Text>
              <Text style={styles.kcal}>{m.kcal} kcal</Text>
            </View>
            <Text style={styles.mealFood}>{m.food}</Text>
            <Text style={styles.mealTag}>{m.tag}</Text>
          </View>
        </View>
      ))}
      <View style={styles.insight}>
        <SymbolView
          name={{ ios: 'sparkles', android: 'auto_awesome', web: 'auto_awesome' }}
          size={16}
          tintColor={DEEP}
          accessible={false}
        />
        <Text style={styles.insightText}>Built around your low Vitamin D and normal glucose.</Text>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: TEAL, overflow: 'hidden' },
  flex: { flex: 1 },
  blob: {
    position: 'absolute',
    width: 360,
    height: 360,
    borderRadius: 180,
    backgroundColor: 'rgba(255,255,255,0.06)',
  },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    minHeight: 44,
  },
  brand: { color: WHITE, fontSize: 20, fontWeight: '700', letterSpacing: 0.5 },
  skip: { minHeight: 44, minWidth: 44, justifyContent: 'center', alignItems: 'flex-end' },
  skipText: { color: WHITE, fontSize: 16, fontWeight: '600' },
  // overflow hidden: the phone mockup is cropped here instead of spilling into the next page
  slide: { paddingHorizontal: 24, paddingTop: 24, gap: 32, overflow: 'hidden' },
  slideBottom: { justifyContent: 'flex-end', paddingBottom: 24 },
  title: { color: WHITE, fontSize: 40, lineHeight: 48, fontWeight: '500' },
  card: { gap: 14, paddingHorizontal: 16, paddingTop: 8 },
  phone: {
    alignSelf: 'center',
    width: 290,
    height: 620,
    padding: 10,
    borderRadius: 52,
    backgroundColor: '#111',
    borderWidth: 2,
    borderColor: '#3A3A3C',
    shadowColor: BLACK,
    shadowOpacity: 0.3,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 12 },
    elevation: 10,
  },
  phoneScreen: { flex: 1, borderRadius: 42, backgroundColor: WHITE, overflow: 'hidden' },
  statusBar: {
    height: 44,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 26,
  },
  time: { color: BLACK, fontSize: 14, fontWeight: '600', width: 40 },
  island: { width: 86, height: 26, borderRadius: 13, backgroundColor: BLACK },
  battery: {
    width: 24,
    height: 12,
    borderRadius: 3,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.4)',
    padding: 1,
    marginLeft: 16,
  },
  batteryFill: { flex: 1, width: '75%', borderRadius: 1.5, backgroundColor: BLACK },
  cardHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 8,
  },
  cardTitle: { flexShrink: 1, color: DEEP, fontSize: 17, fontWeight: '700' },
  example: { color: 'rgba(0,0,0,0.55)', fontSize: 12, fontWeight: '600' },
  rowName: { color: 'rgba(0,0,0,0.6)', fontSize: 13 },
  rowValue: { color: BLACK, fontSize: 16, fontWeight: '600', marginTop: 2 },
  pill: {
    fontSize: 13,
    fontWeight: '700',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    overflow: 'hidden',
  },
  pillOk: { color: DEEP, backgroundColor: '#D7F0EE' },
  pillLow: { color: AMBER, backgroundColor: '#FFE7D1' },
  summary: { flexDirection: 'row', gap: 8 },
  marker: { gap: 2 },
  markerHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  unit: { color: 'rgba(0,0,0,0.55)', fontSize: 13, fontWeight: '500' },
  status: { fontSize: 12, fontWeight: '700' },
  statusOk: { color: TEAL_TEXT },
  statusLow: { color: AMBER },
  track: { height: 6, borderRadius: 3, backgroundColor: '#ECEFF0', marginTop: 8 },
  normalZone: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    borderRadius: 3,
    backgroundColor: '#BFE5E1',
  },
  thumb: {
    position: 'absolute',
    top: -4,
    width: 14,
    height: 14,
    marginLeft: -7,
    borderRadius: 7,
    borderWidth: 3,
    borderColor: WHITE,
  },
  thumbOk: { backgroundColor: TEAL },
  thumbLow: { backgroundColor: '#E07A1F' },
  meal: { flexDirection: 'row', gap: 12, alignItems: 'flex-start' },
  mealIcon: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: '#EAF6F5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mealFood: { color: BLACK, fontSize: 15, fontWeight: '600', marginTop: 2 },
  kcal: { color: 'rgba(0,0,0,0.6)', fontSize: 12, fontWeight: '600' },
  mealTag: {
    alignSelf: 'flex-start',
    marginTop: 6,
    color: TEAL_TEXT,
    fontSize: 11,
    fontWeight: '700',
    backgroundColor: '#EAF6F5',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 999,
    overflow: 'hidden',
  },
  insight: {
    flexDirection: 'row',
    gap: 8,
    alignItems: 'flex-start',
    backgroundColor: '#EAF6F5',
    borderRadius: 14,
    padding: 12,
  },
  insightText: { flex: 1, color: DEEP, fontSize: 13, lineHeight: 18, fontWeight: '500' },
  bottomBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: 16,
  },
  dots: { flexDirection: 'row', gap: 6 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: 'rgba(255,255,255,0.4)' },
  dotOn: { width: 24, backgroundColor: WHITE },
  next: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: BLACK,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cta: {
    height: 60,
    borderRadius: 30,
    paddingHorizontal: 28,
    backgroundColor: BLACK,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  ctaText: { color: WHITE, fontSize: 17, fontWeight: '700' },
  pressed: { opacity: 0.8 },
  signIn: { minHeight: 44, justifyContent: 'center', alignItems: 'center', marginTop: 8 },
  signInText: { color: WHITE, fontSize: 15 },
  signInBold: { fontWeight: '700', textDecorationLine: 'underline' },
});
