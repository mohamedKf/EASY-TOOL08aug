
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  runApp(const EasyToolWorkerApp());
}

class EasyToolWorkerApp extends StatelessWidget {
  const EasyToolWorkerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Easy Tool Worker',
      theme: ThemeData(primarySwatch: Colors.blue),
      initialRoute: '/login',
      routes: {
        '/login': (context) => const LoginPage(),
        '/signup': (context) => const SignUpPage(),
        '/home': (context) => const HomePage(),
        '/projects': (context) => const ProjectsPage(),
        '/messages': (context) => const MessagesPage(),
        '/reports': (context) => const ReportsPage(),
      },
    );
  }
}

//////////////////// LOGIN PAGE ////////////////////
class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final usernameController = TextEditingController();
  final passwordController = TextEditingController();
  bool isLoading = false;
  String? errorMessage;

  Future<void> loginWorker() async {
    setState(() {
      isLoading = true;
      errorMessage = null;
    });

    final url = Uri.parse('http://10.0.2.2:8000/api/worker-login/');
    // Use 10.0.2.2 for Android Emulator; if using real phone, use your laptop's IP

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': usernameController.text,
          'password': passwordController.text,
        }),
      );

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 && data['status'] == 'success') {
        SharedPreferences prefs = await SharedPreferences.getInstance();
        await prefs.setString('token', data['token']);
        await prefs.setString('username', data['user']['username']);
        await prefs.setInt('user_id', data['user']['id']);

        Navigator.pushReplacementNamed(context, '/home');
      } else {
        setState(() {
          errorMessage = data['message'] ?? 'Login failed';
        });
      }
    } catch (e) {
      setState(() {
        errorMessage = 'Error: $e';
      });
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Worker Login')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(controller: usernameController, decoration: const InputDecoration(labelText: 'Username')),
            const SizedBox(height: 10),
            TextField(controller: passwordController, obscureText: true, decoration: const InputDecoration(labelText: 'Password')),
            const SizedBox(height: 20),
            if (errorMessage != null) Text(errorMessage!, style: const TextStyle(color: Colors.red)),
            isLoading
                ? const CircularProgressIndicator()
                : ElevatedButton(
                    onPressed: loginWorker,
                    child: const Text('Login'),
                  ),
            TextButton(
              onPressed: () => Navigator.pushNamed(context, '/signup'),
              child: const Text("Don't have an account? Sign up"),
            ),
          ],
        ),
      ),
    );
  }
}
//////////////////// SIGN-UP PAGE ////////////////////
class SignUpPage extends StatelessWidget {
  const SignUpPage({super.key});

  @override
  Widget build(BuildContext context) {
    final usernameController = TextEditingController();
    final passwordController = TextEditingController();
    final companyCodeController = TextEditingController();

    return Scaffold(
      appBar: AppBar(title: const Text('Worker Sign-Up')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(controller: usernameController, decoration: const InputDecoration(labelText: 'Username')),
            const SizedBox(height: 10),
            TextField(controller: passwordController, obscureText: true, decoration: const InputDecoration(labelText: 'Password')),
            const SizedBox(height: 10),
            TextField(controller: companyCodeController, decoration: const InputDecoration(labelText: 'Company Code')),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(context); // back to login
              },
              child: const Text('Sign Up'),
            ),
          ],
        ),
      ),
    );
  }
}



class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  bool clockedIn = false;

  // Placeholder stats
  int totalDays = 5;
  double totalHours = 38.5;

  // Placeholder attendance data
  List<Map<String, String>> attendanceHistory = [
    {
      "date": "2025-08-01",
      "clockIn": "08:05",
      "clockInLocation": "Site A",
      "clockOut": "17:15",
      "clockOutLocation": "Site A",
      "hours": "9.1"
    },
    {
      "date": "2025-08-02",
      "clockIn": "08:10",
      "clockInLocation": "Site B",
      "clockOut": "17:00",
      "clockOutLocation": "Site B",
      "hours": "8.8"
    },
  ];

  void toggleClockInOut() {
    setState(() {
      clockedIn = !clockedIn;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(clockedIn ? "Clocked In" : "Clocked Out")),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Worker Dashboard')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Big circle button
            GestureDetector(
              onTap: toggleClockInOut,
              child: Container(
                width: 150,
                height: 150,
                decoration: BoxDecoration(
                  color: clockedIn ? Colors.red : Colors.green,
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: Text(
                    clockedIn ? "Clock Out" : "Clock In",
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Stats section
            Card(
              elevation: 2,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Text("Days worked this month: $totalDays", style: const TextStyle(fontSize: 16)),
                    const SizedBox(height: 8),
                    Text("Total hours this month: $totalHours", style: const TextStyle(fontSize: 16)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Attendance table
            const Text("Attendance History", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            Table(
              border: TableBorder.all(color: Colors.grey),
              columnWidths: const {
                0: FlexColumnWidth(1.2),
                1: FlexColumnWidth(1.2),
                2: FlexColumnWidth(1.5),
                3: FlexColumnWidth(1.2),
                4: FlexColumnWidth(1.5),
                5: FlexColumnWidth(1.0),
              },
              children: [
                const TableRow(
                  decoration: BoxDecoration(color: Colors.blueGrey),
                  children: [
                    Padding(padding: EdgeInsets.all(4), child: Text("Date", style: TextStyle(color: Colors.white))),
                    Padding(padding: EdgeInsets.all(4), child: Text("In", style: TextStyle(color: Colors.white))),
                    Padding(padding: EdgeInsets.all(4), child: Text("In Loc", style: TextStyle(color: Colors.white))),
                    Padding(padding: EdgeInsets.all(4), child: Text("Out", style: TextStyle(color: Colors.white))),
                    Padding(padding: EdgeInsets.all(4), child: Text("Out Loc", style: TextStyle(color: Colors.white))),
                    Padding(padding: EdgeInsets.all(4), child: Text("Hrs", style: TextStyle(color: Colors.white))),
                  ],
                ),
                for (var a in attendanceHistory)
                  TableRow(
                    children: [
                      Padding(padding: const EdgeInsets.all(4), child: Text(a["date"]!)),
                      Padding(padding: const EdgeInsets.all(4), child: Text(a["clockIn"]!)),
                      Padding(padding: const EdgeInsets.all(4), child: Text(a["clockInLocation"]!)),
                      Padding(padding: const EdgeInsets.all(4), child: Text(a["clockOut"]!)),
                      Padding(padding: const EdgeInsets.all(4), child: Text(a["clockOutLocation"]!)),
                      Padding(padding: const EdgeInsets.all(4), child: Text(a["hours"]!)),
                    ],
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

//////////////////// PROJECTS PAGE ////////////////////
class ProjectsPage extends StatelessWidget {
  const ProjectsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Projects')),
      body: const Center(child: Text('Project list will appear here')),
    );
  }
}

//////////////////// MESSAGES PAGE ////////////////////
class MessagesPage extends StatelessWidget {
  const MessagesPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Messages')),
      body: const Center(child: Text('Messages will appear here')),
    );
  }
}

//////////////////// REPORTS PAGE ////////////////////
class ReportsPage extends StatelessWidget {
  const ReportsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reports')),
      body: const Center(child: Text('Reports will appear here')),
    );
  }
}

