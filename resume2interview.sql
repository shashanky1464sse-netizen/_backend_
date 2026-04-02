-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3307
-- Generation Time: Apr 02, 2026 at 04:56 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `resume2interview`
--

-- --------------------------------------------------------

--
-- Table structure for table `alembic_version`
--

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `alembic_version`
--

INSERT INTO `alembic_version` (`version_num`) VALUES
('1b377095c9c8');

-- --------------------------------------------------------

--
-- Table structure for table `interviews`
--

CREATE TABLE `interviews` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `feedback_level` varchar(50) NOT NULL,
  `score` int(11) NOT NULL,
  `summary` text NOT NULL,
  `created_at` datetime NOT NULL,
  `total_questions` int(11) DEFAULT NULL,
  `role_applied_for` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `interviews`
--

INSERT INTO `interviews` (`id`, `user_id`, `feedback_level`, `score`, `summary`, `created_at`, `total_questions`, `role_applied_for`) VALUES
(60, 33, 'Needs Improvement', 0, 'Candidate demonstrated no strengths and significant weaknesses in all technical areas, lacking essential skills for an iOS Application Developer role.', '2026-03-30 07:26:09', 10, 'iOS Application Developer'),
(62, 35, 'Needs Improvement', 0, 'The candidate demonstrated no strengths and significant weaknesses in all technical areas, lacking essential skills for a Data Scientist role.', '2026-03-31 04:00:26', 10, 'Data Scientist'),
(63, 35, 'Needs Improvement', 0, 'The candidate demonstrated no strength and significant weaknesses in all technical areas, lacking essential iOS development skills in Swift and related technologies.', '2026-03-31 08:33:22', 10, 'iOS Application Developer'),
(64, 35, 'Needs Improvement', 1, 'The candidate showed basic Swift skills but lacked proficiency in essential iOS development tools and concepts, including Git, REST API, and unit testing, indicating significant gaps in their qualifications for the iOS Application Developer role.', '2026-03-31 08:44:44', 10, 'iOS Application Developer'),
(65, 35, 'Needs Improvement', 0, 'The candidate demonstrated no strength and significant weakness in all technical areas, lacking essential skills for a Software Developer role.', '2026-03-31 09:55:35', 10, 'Software Developer');

-- --------------------------------------------------------

--
-- Table structure for table `question_answers`
--

CREATE TABLE `question_answers` (
  `id` int(11) NOT NULL,
  `interview_id` int(11) NOT NULL,
  `question` text NOT NULL,
  `answer` text NOT NULL,
  `category` varchar(100) NOT NULL,
  `score` int(11) DEFAULT NULL,
  `strengths` text DEFAULT NULL,
  `improvements` text DEFAULT NULL,
  `suggestions` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `question_answers`
--

INSERT INTO `question_answers` (`id`, `interview_id`, `question`, `answer`, `category`, `score`, `strengths`, `improvements`, `suggestions`) VALUES
(546, 60, 'How do you optimize the performance of a Data Visualization dashboard when dealing with large datasets, and what tools or libraries would you use to achieve this?', 'i don\'t know ', 'Data Visualization', 0, '[\"Good effort.\"]', '[\"Lack of knowledge in data visualization optimization\", \"Unfamiliarity with relevant tools and libraries\"]', '[\"Research and learn about data visualization optimization techniques\", \"Familiarize yourself with libraries such as D3.js or Chart.js for web-based visualizations, and iOS-specific libraries like Core Plot or SwiftCharts for mobile development\", \"Investigate data aggregation, filtering, and sampling methods to reduce dataset size and improve performance\", \"Consider using iOS-specific features like Core Animation and Core Graphics to enhance visualization performance\"]'),
(547, 60, 'Can you explain how you would handle data aggregation and filtering in this scenario to ensure the dashboard remains responsive?', 'No answer provided.', 'Data Visualization', 0, '[\"Good effort.\"]', '[\"Provide a clear explanation of data aggregation and filtering techniques\", \"Explain how to optimize dashboard performance\", \"Describe experience with relevant data visualization tools and technologies\"]', '[\"Research and review iOS data visualization frameworks such as Chart.js or SwiftUI Charts\", \"Practice explaining technical concepts clearly and concisely\", \"Review common data aggregation and filtering techniques such as grouping, sorting, and filtering to improve data visualization skills\"]'),
(548, 60, 'Describe a situation where you would use a Recommendation System in a mobile application, and how you would implement it using Swift and SwiftUI', 'No answer provided.', 'Recommendation Systems', 0, '[\"Good effort.\"]', '[\"Provide a clear understanding of Recommendation Systems\", \"Explain the use case for a mobile application\", \"Describe the implementation using Swift and SwiftUI\"]', '[\"Research and learn about Recommendation Systems and their applications\", \"Familiarize yourself with Swift and SwiftUI to implement a basic Recommendation System\", \"Practice explaining technical concepts and providing example use cases for mobile applications\"]'),
(549, 60, 'How would you handle user feedback and update the recommendation model to improve its accuracy over time?', 'No answer provided.', 'Recommendation Systems', 0, '[\"Good effort.\"]', '[\"Provide a basic understanding of recommendation systems\", \"Explain the importance of user feedback in improving model accuracy\", \"Describe a general approach to updating a recommendation model\"]', '[\"Research collaborative filtering and content-based filtering techniques\", \"Familiarize yourself with A/B testing and its application in evaluating model updates\", \"Investigate how iOS applications can collect and incorporate user feedback to improve recommendation models\"]'),
(550, 60, 'Explain how you would design a REST API to interact with a MySQL database, and how you would handle errors and exceptions in this API', 'No answer provided.', 'REST API', 0, '[\"Good effort.\"]', '[\"Provide a basic understanding of REST API design\", \"Explain how to interact with a MySQL database\", \"Describe error and exception handling mechanisms\"]', '[\"Study REST API principles and HTTP request methods\", \"Research MySQL database integration with REST API\", \"Review error handling best practices for REST APIs, such as using HTTP status codes and error response bodies\", \"Practice designing and implementing REST APIs with error handling for a MySQL database\"]'),
(551, 60, 'Can you describe how you would implement authentication and authorization in this API to ensure secure data access?', 'No answer provided.', 'REST API', 0, '[\"Good effort.\"]', '[\"Provide a basic understanding of authentication and authorization concepts\", \"Explain the importance of secure data access in REST APIs\", \"Describe common authentication protocols such as OAuth, JWT, or Basic Auth\"]', '[\"Research and review common authentication and authorization methods for REST APIs\", \"Review Apple\'s guidelines for secure networking in iOS applications\", \"Practice explaining technical concepts clearly and concisely for future interviews\"]'),
(552, 60, 'How do you approach Unit Testing in a Swift application using Xcode, and what strategies do you use to ensure thorough test coverage?', 'No answer provided.', 'Unit Testing', 0, '[\"Good effort.\"]', '[\"Lack of understanding of Unit Testing in Swift\", \"Inability to articulate testing strategies\", \"Failure to provide examples of test coverage techniques\"]', '[\"Review Xcode\'s built-in Unit Testing framework and learn how to write test cases in Swift\", \"Study testing strategies such as TDD, BDD, and black box testing\", \"Practice writing unit tests for Swift applications to improve test coverage and ensure code reliability\"]'),
(553, 60, 'Can you explain how you would test a complex UI component, such as a custom table view cell, using XCTest and UIKit?', 'No answer provided.', 'Unit Testing', 0, '[\"Good effort.\"]', '[\"Provide a basic understanding of XCTest and UIKit\", \"Explain the concept of unit testing for UI components\", \"Describe a general approach to testing a custom table view cell\"]', '[\"Familiarize yourself with XCTest framework and its application in iOS development\", \"Review Apple\'s documentation on UIKit and XCTest for testing UI components\", \"Practice writing unit tests for custom UI components using XCTest and UIKit\"]'),
(554, 60, 'Describe a scenario where you would use System Design principles to architect a scalable mobile application, and how you would apply Modular Architecture and Design Patterns to achieve this', 'No answer provided.', 'System Design', 0, '[\"Good effort.\"]', '[\"Lack of understanding of System Design principles\", \"Inability to apply Modular Architecture and Design Patterns\", \"Failure to provide a scenario for scalable mobile application architecture\"]', '[\"Study and review System Design principles for mobile applications\", \"Research and practice applying Modular Architecture and Design Patterns in iOS development\", \"Prepare to describe a scenario where scalability is crucial and explain how to achieve it using industry-standard design principles and patterns\"]'),
(555, 60, 'How would you handle communication between modules in this architecture, and what mechanisms would you use to ensure loose coupling and high cohesion?', 'fine Kaushal pundamave', 'System Design', 0, '[\"Good effort.\"]', '[\"Lack of understanding of system design principles\", \"Inability to articulate design decisions\", \"Failure to provide relevant technical terms or concepts\"]', '[\"Study iOS architecture patterns such as MVC, MVP, and MVVM\", \"Learn about dependency injection and service locators for loose coupling\", \"Research design principles like SOLID and apply them to iOS development\", \"Practice explaining technical concepts and design decisions clearly and concisely\"]'),
(566, 62, 'How would you optimize the performance of a SQL query that is retrieving a large amount of data from an Oracle database, and what indexing strategies would you use?', 'No answer provided.', 'SQL Querying', 0, '[\"Good effort.\"]', '[\"Provide a basic understanding of SQL query optimization\", \"Explain indexing strategies for Oracle databases\", \"Discuss the importance of efficient data retrieval for data science tasks\"]', '[\"Research and understand the fundamentals of SQL query optimization\", \"Familiarize yourself with Oracle database indexing strategies, such as B-tree and bitmap indexing\", \"Practice optimizing SQL queries for large datasets to improve data retrieval efficiency as a data scientist\"]'),
(567, 62, 'Can you explain how you would monitor the performance of the query and what tools you would use to identify bottlenecks?', 'No answer provided.', 'SQL Querying', 0, '[\"Good effort.\"]', '[\"Provide a clear and concise explanation of query performance monitoring\", \"Familiarize themselves with industry-standard tools for bottleneck identification\", \"Demonstrate understanding of database optimization techniques\"]', '[\"Study SQL query optimization techniques\", \"Familiarize themselves with tools like EXPLAIN, EXPLAIN ANALYZE, and pg_stat_statements\", \"Practice monitoring query performance using database administration tools\"]'),
(568, 62, 'Given a dataset with missing values, how would you handle the missing data using data analysis techniques, and what methods would you use to impute the missing values?', 'No answer provided.', 'Data Analysis', 0, '[\"Good effort.\"]', '[\"Provide a clear and concise answer to the question\", \"Demonstrate knowledge of data analysis techniques for handling missing values\", \"Explain methods for imputing missing values\"]', '[\"Familiarize yourself with industry-standard methods for handling missing data, such as mean/median/mode imputation, regression imputation, and K-Nearest Neighbors imputation\", \"Review data analysis techniques, including data cleaning, feature scaling, and data transformation\", \"Practice explaining complex technical concepts in a clear and concise manner, tailored to a Data Scientist role\"]'),
(569, 62, 'Can you describe a situation where you would use a specific imputation method, such as mean or median imputation, and why you would choose that method over others?', 'No answer provided.', 'Data Analysis', 0, '[\"Good effort.\"]', '[\"Provide a clear understanding of imputation methods\", \"Explain the context in which a specific imputation method is chosen\", \"Demonstrate knowledge of the advantages and disadvantages of different imputation techniques\"]', '[\"Review the different types of imputation methods, such as mean, median, and imputation using regression\", \"Practice explaining the reasoning behind choosing a specific imputation method for a given scenario\", \"Consider discussing the importance of understanding the data distribution and the potential impact of imputation on model performance\"]'),
(570, 62, 'How would you design a data visualization dashboard using a Java-based tool, such as JFreeChart or XChart, to display complex data insights to a non-technical audience?', 'No answer provided.', 'Data Visualization', 0, '[\"Good effort.\"]', '[\"Provide a basic understanding of data visualization principles\", \"Familiarize themselves with Java-based data visualization tools such as JFreeChart or XChart\", \"Develop skills to explain technical concepts to non-technical audiences\"]', '[\"Research and review documentation for JFreeChart or XChart to understand their capabilities and limitations\", \"Practice designing sample dashboards using Java-based tools to improve their skills\", \"Focus on learning how to effectively communicate complex data insights to non-technical stakeholders\"]'),
(571, 62, 'Can you walk me through your process for selecting the most appropriate visualization type, such as a bar chart or scatter plot, for a given dataset and audience?', 'No answer provided.', 'Data Visualization', 0, '[\"Good effort.\"]', '[\"Provide a clear and concise answer to the question\", \"Demonstrate knowledge of different visualization types and their use cases\", \"Show understanding of the importance of considering the audience and dataset when selecting a visualization\"]', '[\"Review common data visualization types and their applications\", \"Practice explaining technical concepts to non-technical audiences\", \"Prepare examples of how to choose appropriate visualizations for different datasets and stakeholders\"]'),
(572, 62, 'Can you explain the concept of convolutional neural networks (CNNs) in computer vision, and how they are used for image classification tasks?', 'No answer provided.', 'Computer Vision', 0, '[\"Good effort.\"]', '[\"Provide a basic definition of convolutional neural networks\", \"Explain the role of convolutional and pooling layers in CNNs\", \"Describe the application of CNNs in image classification tasks\"]', '[\"Review the fundamental concepts of computer vision and deep learning\", \"Familiarize yourself with popular CNN architectures such as LeNet, AlexNet, and ResNet\", \"Practice explaining technical concepts in a clear and concise manner to improve communication skills\"]'),
(573, 62, 'How would you implement a CNN using a programming language like C++, and what considerations would you take into account when selecting a deep learning framework?', 'No answer provided.', 'Computer Vision', 0, '[\"Good effort.\"]', '[\"Provide a basic understanding of CNN implementation\", \"Discuss considerations for selecting a deep learning framework\", \"Familiarity with C++ and deep learning frameworks\"]', '[\"Research and review the basics of CNN architecture and implementation\", \"Investigate popular deep learning frameworks such as TensorFlow or PyTorch and their C++ APIs\", \"Practice implementing simple CNN models using C++ and a chosen framework to gain hands-on experience\"]'),
(574, 62, 'How would you design a database schema to store and manage large amounts of data in an Oracle database, and what considerations would you take into account when selecting data types and indexing strategies?', 'No answer provided.', 'Oracle', 0, '[\"Good effort.\"]', '[\"Provide a basic understanding of database schema design\", \"Explain considerations for selecting data types\", \"Discuss indexing strategies for large datasets\"]', '[\"Familiarize yourself with Oracle database architecture and data types\", \"Research best practices for database schema design and indexing\", \"Practice designing and implementing database schemas for large datasets as a Data Scientist\"]'),
(575, 62, 'Can you describe a situation where you would use a specific database design pattern, such as star or snowflake schema, and why you would choose that pattern over others?', 'No answer provided.', 'Oracle', 0, '[\"Good effort.\"]', '[\"Provide a basic understanding of database design patterns\", \"Familiarize with star and snowflake schema\", \"Develop ability to apply database design patterns to real-world scenarios\"]', '[\"Study database design patterns and their applications\", \"Practice designing databases for various use cases\", \"Review data warehousing concepts and ETL processes relevant to data science role\"]'),
(576, 63, 'What is the difference between var, let, and constant in Swift?', 'xqwx', 'Swift', 0, '[\"Good effort.\"]', '[\"Lack of understanding of Swift basics\", \"Failure to provide a relevant answer\"]', '[\"Review the Swift documentation on variable declarations\", \"Practice explaining the difference between var, let, and constant in Swift\", \"Focus on providing clear and concise answers to technical questions\"]'),
(577, 63, 'Can you provide an example of when you would use each?', 'xqsxq', 'Swift', 0, '[\"Good effort.\"]', '[\"Lack of understanding of the question\", \"Failure to provide a relevant example\", \"Inability to communicate technical concepts effectively\"]', '[\"Review the fundamentals of Swift programming language\", \"Practice explaining technical concepts in a clear and concise manner\", \"Prepare examples of common iOS development scenarios to demonstrate problem-solving skills\"]'),
(578, 63, 'How do you handle errors in PHP?', 'saxasxa', 'PHP', 0, '[\"Good effort.\"]', '[\"Lack of relevant knowledge in PHP\", \"Failure to provide a coherent answer\", \"Inability to demonstrate error handling skills\"]', '[\"Study PHP error handling mechanisms, such as try-catch blocks and error types\", \"Review industry standards for error handling in PHP, such as logging and error reporting\", \"Prepare to answer technical questions relevant to the iOS Application Developer role, focusing on Swift or Objective-C error handling instead of PHP\"]'),
(579, 63, 'What is the difference between try-catch and error handling using if-else statements?', 'xz', 'PHP', 0, '[\"Good effort.\"]', '[\"Lack of relevant knowledge in PHP\", \"Failure to address the question\", \"No indication of understanding error handling concepts\"]', '[\"Study PHP basics, including error handling mechanisms\", \"Review differences between try-catch blocks and if-else statements for error handling\", \"Prepare to answer technical questions relevant to the iOS Application Developer role, focusing on Swift or Objective-C rather than PHP\"]'),
(580, 63, 'What is the purpose of Git in the development process?', 'sc cs', 'Git', 0, '[\"Good effort.\"]', '[\"Lack of understanding of Git basics\", \"Inability to articulate the purpose of Git\", \"Unrelated response to the question\"]', '[\"Study the fundamentals of Git and its role in version control\", \"Review how Git is used in the iOS development process\", \"Prepare to provide clear and concise answers to technical questions related to Git and iOS development\"]'),
(581, 63, 'Can you explain the difference between Git fetch and Git pull?', 'sdsd sd', 'Git', 0, '[\"Good effort.\"]', '[\"Provide a clear and concise answer\", \"Understand the basics of Git commands\", \"Familiarize yourself with Git workflow\"]', '[\"Review the official Git documentation to understand the difference between Git fetch and Git pull\", \"Practice using Git commands in a real-world project to gain hands-on experience\", \"Focus on learning the fundamentals of Git as it is a crucial tool for any iOS Application Developer\"]'),
(582, 63, 'How do you structure a REST API endpoint?', 'ds sd', 'REST API', 0, '[\"Good effort.\"]', '[\"Lack of understanding of REST API endpoint structure\", \"Failure to provide a coherent answer\"]', '[\"Study the basic principles of REST API design\", \"Review HTTP request methods and their uses\", \"Practice designing and implementing REST API endpoints in iOS applications\"]'),
(583, 63, 'What HTTP methods would you use for creating, reading, updating, and deleting resources?', 'ds sd', 'REST API', 0, '[\"Good effort.\"]', '[\"Lack of understanding of HTTP methods\", \"Inability to provide a clear and concise answer\", \"Failure to demonstrate knowledge of REST API fundamentals\"]', '[\"Study the basics of REST API and HTTP methods such as POST, GET, PUT/PATCH, and DELETE\", \"Review the role of each HTTP method in CRUD operations\", \"Practice explaining technical concepts clearly and concisely to improve communication skills\"]'),
(584, 63, 'How do you send and receive data in JSON format using Swift?', 'd sd s', 'JSON', 0, '[\"Good effort.\"]', '[\"Lack of relevant technical knowledge\", \"Inability to provide a clear and concise answer\", \"Failure to demonstrate understanding of JSON and Swift\"]', '[\"Review Swift documentation for JSON encoding and decoding\", \"Familiarize yourself with URLSession and Codable protocols\", \"Practice implementing JSON data transfer in a Swift-based iOS application\"]'),
(585, 63, 'What is the difference between JSONSerialization and Codable?', 'ds  sd', 'JSON', 0, '[\"Good effort.\"]', '[\"Provide a clear and concise answer\", \"Demonstrate knowledge of JSONSerialization and Codable\", \"Explain the difference between the two\"]', '[\"Study the differences between JSONSerialization and Codable in Swift\", \"Practice explaining technical concepts in a clear and concise manner\", \"Review the official Apple documentation for JSONSerialization and Codable to better understand their usage in iOS development\"]'),
(586, 64, 'How do you handle errors in Swift, and what are some best practices for error handling in a SwiftUI application?', 'error handle use auto generation and verfiy the data', 'Swift', 10, '[\"Good effort.\"]', '[\"Lack of understanding of error handling mechanisms in Swift\", \"Insufficient knowledge of best practices for error handling in SwiftUI\", \"Poor communication skills\"]', '[\"Study Swift\'s error handling mechanisms, such as try-catch blocks and error types\", \"Learn about SwiftUI\'s built-in error handling features, such as the .error modifier\", \"Practice explaining technical concepts clearly and concisely\", \"Review Apple\'s documentation on error handling in Swift and SwiftUI\", \"Implement error handling in a sample SwiftUI project to gain hands-on experience\"]'),
(587, 64, 'Can you give an example of how you would use a try-catch block to handle a specific error in a SwiftUI view model?', 'mvvm', 'Swift', 0, '[\"Good effort.\"]', '[\"Lack of understanding of try-catch blocks in Swift\", \"Failure to provide a relevant example\", \"Insufficient knowledge of SwiftUI view models\"]', '[\"Study the basics of error handling in Swift, including try-catch blocks and error types\", \"Review the architecture of SwiftUI view models and their role in handling errors\", \"Practice implementing try-catch blocks in SwiftUI view models to handle specific errors, such as networking or data parsing errors\"]'),
(588, 64, 'What is the purpose of Git, and how do you use it for version control in a team environment?', 'no', 'Git', 0, '[\"Good effort.\"]', '[\"Lack of understanding of Git and its purpose\", \"Inability to explain version control in a team environment\"]', '[\"Study the basics of Git and its application in version control\", \"Learn how to initialize and manage Git repositories\", \"Understand how to collaborate with team members using Git\", \" Familiarize yourself with Git commands and best practices for iOS development teams\"]'),
(589, 64, 'How do you resolve conflicts that arise when merging branches in Git, and what strategies do you use to avoid conflicts in the first place?', 'it;fig', 'Git', 0, '[\"Good effort.\"]', '[\"Provide a clear and concise answer\", \"Demonstrate understanding of Git conflict resolution\", \"Explain strategies for avoiding conflicts\"]', '[\"Study Git documentation and practice resolving conflicts\", \"Learn about Git merge strategies and tools like git merge --abort or git merge --continue\", \"Understand how to use git diff and git status to identify and resolve conflicts in iOS development projects\"]'),
(590, 64, 'What are some key principles of Data Visualization, and how do you apply them when creating visualizations for a mobile application?', 'vd', 'Data Visualization', 0, '[\"Good effort.\"]', '[\"Lack of understanding of data visualization principles\", \"Inability to provide relevant examples\", \"Failure to demonstrate knowledge of mobile application development\"]', '[\"Study key principles of data visualization such as clarity, accuracy, and aesthetics\", \"Research how to apply these principles in a mobile application context\", \"Practice creating visualizations for mobile applications using tools like Swift UI or third-party libraries\", \"Review industry standards for data visualization in mobile applications, such as those provided by Apple or Google\"]'),
(591, 64, 'How do you choose the most effective chart type for a given dataset, and what considerations do you take into account when designing a visualization for a small screen?', 'v', 'Data Visualization', 0, '[\"Good effort.\"]', '[\"Lack of understanding of data visualization principles\", \"Inability to articulate considerations for small screen design\", \"Failure to provide examples of effective chart types\"]', '[\"Study data visualization best practices, such as those outlined by Edward Tufte or Stephen Few\", \"Research iOS-specific design guidelines for small screens, including Apple\'s Human Interface Guidelines\", \"Practice designing and implementing different chart types, such as bar charts, line charts, and scatter plots, using iOS frameworks like UIKit or third-party libraries like Charts or Plot\"]'),
(592, 64, 'What is a REST API, and how do you use it to interact with a backend service from a mobile application?', 'fvevfev', 'REST API', 0, '[\"Good effort.\"]', '[\"Provide a clear and concise definition of REST API\", \"Explain the basic principles of REST API\", \"Describe how to use REST API in a mobile application\"]', '[\"Study the fundamentals of REST API and its application in mobile development\", \"Review iOS networking frameworks such as URLSession or third-party libraries like Alamofire\", \"Practice implementing REST API calls in a mobile application using Swift or other relevant programming languages\"]'),
(593, 64, 'Can you describe how you would handle authentication and authorization when making requests to a REST API from a mobile app?', 'verfd', 'REST API', 0, '[\"Good effort.\"]', '[\"Provide a clear and concise answer\", \"Demonstrate knowledge of authentication and authorization concepts\", \"Explain how to handle authentication and authorization in a mobile app\"]', '[\"Study REST API security best practices\", \"Research OAuth, JWT, and other authentication protocols\", \"Learn how to implement secure authentication and authorization in an iOS application using Swift or Objective-C\"]'),
(594, 64, 'How do you approach testing a new feature in a mobile application, and what types of tests do you typically write?', 'berbebt', 'Unit Testing', 0, '[\"Good effort.\"]', '[\"Provide a clear and concise answer\", \"Explain the approach to testing a new feature\", \"Mention types of tests typically written\"]', '[\"Study the different types of tests such as unit tests, integration tests, and UI tests\", \"Learn about testing frameworks like XCTest and how to write test cases\", \"Practice writing tests for a mobile application to improve understanding of testing concepts\"]'),
(595, 64, 'Can you give an example of how you would write a unit test for a specific piece of functionality in a SwiftUI view model using XCTest?', 'vbrebtrebtr', 'Unit Testing', 0, '[\"Good effort.\"]', '[\"Provide a relevant and accurate code example\", \"Demonstrate understanding of XCTest and unit testing principles\", \"Show familiarity with SwiftUI view models\"]', '[\"Review Apple\'s official documentation on XCTest and unit testing in SwiftUI\", \"Practice writing unit tests for view models using XCTest\", \"Familiarize yourself with SwiftUI view model architecture and best practices\"]'),
(596, 65, 'What is the purpose of the @SpringBootApplication annotation in a Spring Boot application?', 'dewdw', 'Spring Boot', 0, '[\"Good effort.\"]', '[\"Lack of understanding of Spring Boot annotations\", \"Failure to provide a relevant answer\", \"No demonstration of knowledge in the area\"]', '[\"Review the purpose and usage of @SpringBootApplication annotation\", \"Study the role of annotations in Spring Boot applications\", \"Prepare to provide clear and concise answers to technical questions related to the position of Software Developer\"]'),
(597, 65, 'Can you explain how it enables auto-configuration?', 'sdsq', 'Spring Boot', 0, '[\"Good effort.\"]', '[\"Lack of understanding of Spring Boot auto-configuration\", \"Inability to provide a clear and concise answer\", \"Failure to demonstrate relevant technical knowledge\"]', '[\"Study the Spring Boot documentation to understand how auto-configuration works\", \"Practice explaining technical concepts in a clear and concise manner\", \"Review the basics of Spring Boot and its features to improve technical knowledge\"]'),
(598, 65, 'How do you create a simple Python function to print \'Hello World\'?', 'saxasx', 'Python', 0, '[\"Good effort.\"]', '[\"Understanding of basic Python syntax\", \"Ability to write simple functions\", \"Familiarity with standard output in Python\"]', '[\"Review the basics of Python programming\", \"Practice writing simple functions with clear and descriptive names\", \"Learn how to use the print function in Python to output strings to the console\"]'),
(599, 65, 'What is the purpose of the print() function in Python?', 'xasxa', 'Python', 0, '[\"Good effort.\"]', '[\"Lack of understanding of basic Python functions\", \"Failure to provide a relevant answer\"]', '[\"Review the basics of Python programming\", \"Familiarize yourself with the print() function and its usage in Python\", \"Practice providing clear and concise answers to technical questions\"]'),
(600, 65, 'What is the difference between \'==\' and \'.equals()\' in Java?', 'saxsa', 'Java', 0, '[\"Good effort.\"]', '[\"Lack of understanding of basic Java concepts\", \"Inability to provide a clear and concise answer\", \"Failure to address the question directly\"]', '[\"Review the basics of Java, including operators and methods\", \"Practice explaining technical concepts in a clear and concise manner\", \"Familiarize yourself with common Java interview questions and practice responding to them accurately\"]'),
(601, 65, 'Can you provide an example where using \'==\' would be incorrect?', 'asxa', 'Java', 0, '[\"Good effort.\"]', '[\"Provide a clear and relevant example\", \"Demonstrate understanding of Java syntax and operators\", \"Communicate effectively and avoid using nonsensical words\"]', '[\"Review Java documentation on equality operators\", \"Practice explaining technical concepts in a clear and concise manner\", \"Prepare examples of common Java pitfalls, such as using \'==\' for object comparison instead of equals() method\"]'),
(602, 65, 'What is the basic structure of an HTML document?', 'xaxa', 'HTML', 0, '[\"Good effort.\"]', '[\"Lack of understanding of HTML basics\", \"Failure to provide a relevant answer\"]', '[\"Review the basic structure of an HTML document, including doctype, html, head, and body tags\", \"Familiarize yourself with standard HTML elements and their uses\", \"Practice explaining technical concepts clearly and concisely\"]'),
(603, 65, 'What is the purpose of the <head> tag in HTML?', 'saxas', 'HTML', 0, '[\"Good effort.\"]', '[\"Lack of understanding of basic HTML tags\", \"Failure to provide a relevant answer\"]', '[\"Review the basics of HTML structure and tags\", \"Familiarize yourself with the purpose and usage of the <head> tag in HTML documents\", \"Practice providing clear and concise answers to technical questions\"]'),
(604, 65, 'What is the purpose of the \'style\' attribute in CSS?', 'xsaxasxsaxasx', 'CSS', 0, '[\"Good effort.\"]', '[\"Provide a clear and concise answer\", \"Understand the basics of CSS\", \"Familiarize with standard CSS attributes\"]', '[\"Review the CSS specification to understand the purpose of the \'style\' attribute\", \"Practice explaining technical concepts in a clear and concise manner\", \"Focus on learning the fundamentals of CSS and its applications in web development\"]'),
(605, 65, 'Can you provide an example of how to use it to change the color of a paragraph?', 'xs zx', 'CSS', 0, '[\"Good effort.\"]', '[\"Provide a relevant and accurate answer\", \"Demonstrate understanding of CSS basics\", \"Use proper terminology and syntax\"]', '[\"Review CSS documentation for text color property\", \"Practice writing simple CSS selectors and properties\", \"Familiarize yourself with standard CSS syntax and examples\"]');

-- --------------------------------------------------------

--
-- Table structure for table `skills`
--

CREATE TABLE `skills` (
  `id` int(11) NOT NULL,
  `interview_id` int(11) NOT NULL,
  `skill_name` varchar(150) NOT NULL,
  `category_score` int(11) DEFAULT NULL,
  `total_questions_per_category` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `skills`
--

INSERT INTO `skills` (`id`, `interview_id`, `skill_name`, `category_score`, `total_questions_per_category`) VALUES
(214, 60, 'Data Visualization', 0, 2),
(215, 60, 'Recommendation Systems', 0, 2),
(216, 60, 'REST API', 0, 2),
(217, 60, 'Unit Testing', 0, 2),
(218, 60, 'System Design', 0, 2),
(224, 62, 'SQL Querying', 0, 2),
(225, 62, 'Data Analysis', 0, 2),
(226, 62, 'Data Visualization', 0, 2),
(227, 62, 'Computer Vision', 0, 2),
(228, 62, 'Oracle', 0, 2),
(229, 63, 'Swift', 0, 2),
(230, 63, 'PHP', 0, 2),
(231, 63, 'Git', 0, 2),
(232, 63, 'REST API', 0, 2),
(233, 63, 'JSON', 0, 2),
(234, 64, 'Swift', 5, 2),
(235, 64, 'Git', 0, 2),
(236, 64, 'Data Visualization', 0, 2),
(237, 64, 'REST API', 0, 2),
(238, 64, 'Unit Testing', 0, 2),
(239, 65, 'Spring Boot', 0, 2),
(240, 65, 'Python', 0, 2),
(241, 65, 'Java', 0, 2),
(242, 65, 'HTML', 0, 2),
(243, 65, 'CSS', 0, 2);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `hashed_password` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL,
  `reset_code` varchar(6) DEFAULT NULL,
  `reset_code_expires_at` datetime DEFAULT NULL,
  `is_verified` tinyint(1) NOT NULL,
  `registration_otp` varchar(6) DEFAULT NULL,
  `registration_otp_expires_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `email`, `hashed_password`, `created_at`, `reset_code`, `reset_code_expires_at`, `is_verified`, `registration_otp`, `registration_otp_expires_at`) VALUES
(25, 'chandanithin07@gmail.com', '$2b$12$n8dxZgRnWWoFTbndf5hAAelaQyuyv77jqQmactSGtuZvM.2ii30z.', '2026-03-24 05:35:41', NULL, NULL, 1, NULL, NULL),
(33, 'lokeshkumar142005@gmail.com', '$2b$12$P4A1QEWjEv.Thvt93R/gvuir90Sezu/Alxiu9XphaL3.nTdzh2pRK', '2026-03-30 07:20:50', NULL, NULL, 1, NULL, NULL),
(35, 'shashanky1464.sse@saveetha.com', '$2b$12$CtbeHiLVpJgWy4kMCQ.dX.UH.ggQM6YaD3xiXTBWP0n8KQVziczMS', '2026-03-31 03:56:43', NULL, NULL, 1, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `user_profiles`
--

CREATE TABLE `user_profiles` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `full_name` varchar(120) DEFAULT NULL,
  `job_title` varchar(120) DEFAULT NULL,
  `location` varchar(120) DEFAULT NULL,
  `bio` text DEFAULT NULL,
  `profile_photo_url` varchar(255) DEFAULT NULL,
  `skills_json` text DEFAULT NULL,
  `previous_role` varchar(100) DEFAULT NULL,
  `target_role` varchar(100) DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `experience_years` int(11) DEFAULT NULL,
  `experience_level` varchar(50) DEFAULT NULL,
  `preferred_difficulty` varchar(20) DEFAULT 'beginner'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user_profiles`
--

INSERT INTO `user_profiles` (`id`, `user_id`, `full_name`, `job_title`, `location`, `bio`, `profile_photo_url`, `skills_json`, `previous_role`, `target_role`, `updated_at`, `experience_years`, `experience_level`, `preferred_difficulty`) VALUES
(24, 25, 'Nithin', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-03-24 05:35:41', NULL, NULL, 'beginner'),
(32, 33, 'lokesh', NULL, NULL, NULL, NULL, '{\"languages\": [\"Swift\", \"PHP\", \"MySQL\", \"Data Visualization\", \"Data Analysis\", \"Recommendation Systems\", \"Image Processing\", \"MVC\", \"MVVM\", \"System Design\", \"Modular Architecture\", \"Design Patterns\"], \"tools_frameworks\": [\"REST API\", \"SwiftUI\", \"UIKit\", \"Xcode\", \"Core Data\", \"Auto Layout\", \"Storyboards\", \"TestFlight\", \"App Store Connect\", \"CI/CD\", \"GitHub Actions\", \"Git\", \"Unit Testing\", \"Apple App Store Connect\"], \"soft_skills\": [\"Problem Solving\", \"Client Communication\", \"Communication\", \"Requirement Analysis\", \"Team Collaboration\", \"Collaboration\", \"Training\", \"Trained\", \"Experienced\"]}', NULL, 'Frontend Developer', '2026-03-30 07:27:54', 2, 'Intermediate', 'advanced'),
(34, 35, 'Shashank', NULL, NULL, NULL, NULL, '{\"languages\": [\"Python\", \"Java\", \"C++\", \"SQL\", \"PostgreSQL\", \"SQL Querying\", \"Database Management\", \"Machine Learning\", \"Data Visualization\", \"Data Analysis\", \"Recommendation Systems\", \"System Design\", \"Design Patterns\", \"Hardware Trojan Detection\", \"Gradient\"], \"tools_frameworks\": [\"HTML\", \"CSS\", \"Spring Boot\", \"AWS\", \"GitHub Actions\", \"Git\", \"GitHub\", \"Unit Testing\", \"Spring\", \"Boot\"], \"soft_skills\": [\"Critical Thinking\", \"Collaboration\", \"Team Collaboration\", \"Teamwork\", \"Analytical Thinking\", \"Support\", \"Design\", \"Problem-solving abilities\", \"Analytical thinking\"]}', NULL, 'Software Developer', '2026-03-31 09:52:27', 0, 'Beginner', 'beginner');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `alembic_version`
--
ALTER TABLE `alembic_version`
  ADD PRIMARY KEY (`version_num`);

--
-- Indexes for table `interviews`
--
ALTER TABLE `interviews`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_interviews_id` (`id`),
  ADD KEY `idx_user_created_at` (`user_id`,`created_at`);

--
-- Indexes for table `question_answers`
--
ALTER TABLE `question_answers`
  ADD PRIMARY KEY (`id`),
  ADD KEY `interview_id` (`interview_id`),
  ADD KEY `ix_question_answers_id` (`id`);

--
-- Indexes for table `skills`
--
ALTER TABLE `skills`
  ADD PRIMARY KEY (`id`),
  ADD KEY `interview_id` (`interview_id`),
  ADD KEY `ix_skills_id` (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_users_email` (`email`),
  ADD KEY `ix_users_id` (`id`);

--
-- Indexes for table `user_profiles`
--
ALTER TABLE `user_profiles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`),
  ADD KEY `ix_user_profiles_id` (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `interviews`
--
ALTER TABLE `interviews`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=71;

--
-- AUTO_INCREMENT for table `question_answers`
--
ALTER TABLE `question_answers`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=656;

--
-- AUTO_INCREMENT for table `skills`
--
ALTER TABLE `skills`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=270;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;

--
-- AUTO_INCREMENT for table `user_profiles`
--
ALTER TABLE `user_profiles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=35;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `interviews`
--
ALTER TABLE `interviews`
  ADD CONSTRAINT `interviews_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `question_answers`
--
ALTER TABLE `question_answers`
  ADD CONSTRAINT `question_answers_ibfk_1` FOREIGN KEY (`interview_id`) REFERENCES `interviews` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `skills`
--
ALTER TABLE `skills`
  ADD CONSTRAINT `skills_ibfk_1` FOREIGN KEY (`interview_id`) REFERENCES `interviews` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `user_profiles`
--
ALTER TABLE `user_profiles`
  ADD CONSTRAINT `user_profiles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
