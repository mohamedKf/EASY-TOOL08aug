import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = "http://192.168.16.48:8000";



  static Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/worker-login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'password': password,
      }),
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> getHomeData() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? token = prefs.getString('token');

    final response = await http.get(
      Uri.parse('$baseUrl/api/worker-home/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> clockIn(double? lat, double? lon) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? token = prefs.getString('token');

    final response = await http.post(
      Uri.parse('$baseUrl/api/worker-clock-in/'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {
        'token': token ?? '',
        'latitude': lat?.toString() ?? '',
        'longitude': lon?.toString() ?? '',
      },
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> clockOut(double? lat, double? lon) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? token = prefs.getString('token');

    final response = await http.post(
      Uri.parse('$baseUrl/api/worker-clock-out/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'token': token,
        'latitude': lat,
        'longitude': lon,
      }),
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> getProjects() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? token = prefs.getString('token');

    final response = await http.get(
      Uri.parse('$baseUrl/api/worker/work-page/'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> getProjectMaterials(int projectId) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? token = prefs.getString('token');

    final response = await http.get(
      Uri.parse('$baseUrl/api/worker/work-page/?project_id=$projectId'),
      headers: {
        'Authorization': 'Token $token',
        'Content-Type': 'application/json',
      },
    );

    return jsonDecode(response.body);
  }

  static Future<void> logout() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? token = prefs.getString('token');

    if (token != null) {
      await http.post(
        Uri.parse('$baseUrl/api/worker-logout/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'token': token}),
      );
    }

    await prefs.clear();
  }
}