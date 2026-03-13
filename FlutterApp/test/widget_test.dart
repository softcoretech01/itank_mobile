// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';

import 'package:iso_tank/main.dart';

void main() {
  testWidgets('App shows login page when not logged in', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp(isLoggedIn: false));

    expect(find.text('Login'), findsOneWidget);
    expect(find.text('iTank'), findsOneWidget);
  });
}
