import 'package:flutter/material.dart';
import 'package:iso_tank/screens/login_page.dart';
import 'package:iso_tank/service/DioProvider.dart';
import 'package:iso_tank/utils/app_colors.dart';
import 'package:flutter_bloc/flutter_bloc.dart';


import 'bloc/tank_inspection/tank_inspection_bloc.dart';
import 'screens/tank_inspection/tank_inspection_flow.dart';
import 'service/ApiClient.dart';
import 'service/secure_storage_service.dart';
import 'repository/auth_repository.dart';

import 'repository/tank_repository.dart';
import 'dart:io';

class MyHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    final client = super.createHttpClient(context);

    // 🔥 Prevent HTTP/2 / keep-alive hanging issues
    client.connectionTimeout = const Duration(seconds: 30);
    client.idleTimeout = const Duration(seconds: 30);
    client.autoUncompress = true;

    return client;
  }
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 🔥 CRITICAL FIX
  HttpOverrides.global = MyHttpOverrides();

  final dio = DioProvider.createDio();
  final apiClient = ApiClient(dio);
  final repo = TankRepository(
    api: apiClient,
    dio: dio, // ✅ SAME DIO
  );
  
  // Register Lifecycle Handler for Auto Logout
  final authRepo = AuthRepository(apiClient);
  WidgetsBinding.instance.addObserver(AppLifecycleHandler(authRepo));

  // Use local auth: if user was previously logged in, go straight to tank inspection
  final isLoggedIn = await secureStorage.getIsLoggedIn();
  final token = await secureStorage.getToken();
  final shouldOpenTankInspection = isLoggedIn && (token != null && token.isNotEmpty);

  runApp(
    MultiBlocProvider(
      providers: [
        BlocProvider(
          create: (_) => TankInspectionBloc(repo),
        ),
      ],
      child: MyApp(
        isLoggedIn: shouldOpenTankInspection,
      ),
    ),
  );
}

// ... existing MyApp and MyHomePage classes ...

class MyApp extends StatelessWidget {
  final bool isLoggedIn;
  final TankRepository? repo;
  
  const MyApp({super.key, required this.isLoggedIn, this.repo});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: AppColors.primary),
      ),
      home: isLoggedIn ? TankInspectionFlow() : LoginPage(),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});
  final String title;
  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  int _counter = 0;
  void _incrementCounter() {
    setState(() {
      _counter++;
    });
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            const Text('You have pushed the button this many times:'),
            Text(
              '$_counter',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _incrementCounter,
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ),
    );
  }
}

class AppLifecycleHandler extends WidgetsBindingObserver {
  final AuthRepository authRepository;

  AppLifecycleHandler(this.authRepository);

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // ⚠️ Previously we logged out on `inactive`, which also fires when app goes to background,
    // causing tokens to be cleared while the user is still in a valid session.
    //
    // To avoid unexpected "Invalid token" errors mid-flow, we now only perform
    // an auto-logout on a hard detach (app is being terminated), and even that
    // can be adjusted later based on UX requirements.
    if (state == AppLifecycleState.detached) {
      authRepository.logout();
    }
  }
}
