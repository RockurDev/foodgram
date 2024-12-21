import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const About = ({ updateOrders, orders }) => {
  return (
    <Main>
      <MetaTags>
        <title>О проекте</title>
        <meta name="description" content="Фудграм - О проекте" />
        <meta property="og:title" content="О проекте" />
      </MetaTags>

      <Container>
        <h1 className={styles.title}>Привет!</h1>
        <div className={styles.content}>
          <div>
            <h2 className={styles.subtitle}>Что это за сайт?</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                <strong>Фудграм</strong> — это уникальная онлайн-платформа, предназначенная для всех любителей
                кулинарии, которые хотят удобно хранить, организовывать и делиться своими любимыми рецептами.
                Проект был создан в рамках курса Яндекс Практикума, но разработка велась полностью самостоятельно,
                с учетом всех современных стандартов веб-разработки.
              </p>
              <p className={styles.textItem}>
                <strong>Уникальность Фудграм</strong> заключается в простоте использования и функциональности. Это
                идеальное место для всех, кто хочет сохранить свои рецепты в одном месте, организовать их по
                категориям и легко делиться с друзьями.
              </p>
              <p className={styles.textItem}>
                Основные возможности, которые предоставляет платформа:
              </p>
              <ul className={styles.textList}>
                <li className={styles.textItem}>
                  <strong>Создание и сохранение рецептов:</strong> пользователи могут легко добавлять новые рецепты,
                  делая процесс готовки еще более увлекательным.
                </li>
                <li className={styles.textItem}>
                  <strong>Обмен рецептами с друзьями:</strong> делитесь своими кулинарными творениями и вдохновляйтесь
                  рецептами от других пользователей.
                </li>
                <li className={styles.textItem}>
                  <strong>Скачивание списка ингредиентов:</strong> создавайте списки покупок с продуктами, необходимыми
                  для приготовления выбранных блюд.
                </li>
                <li className={styles.textItem}>
                  <strong>Избранное:</strong> добавляйте любимые рецепты в избранное, чтобы всегда иметь их под рукой.
                </li>
              </ul>
              <p className={styles.textItem}>
                Для полного доступа ко всем функциям требуется <strong>регистрация</strong>. Стоит отметить, что
                <strong>проверка email не требуется</strong>, так что можно сразу приступить к использованию платформы,
                без лишних шагов.
              </p>
              <p className={styles.textItem}>
                <strong>Фудграм</strong> — это не просто сайт для рецептов. Это сообщество, где каждый может поделиться
                своим кулинарным вдохновением, узнать новые идеи для ужинов, создать собственную кулинарную книгу и
                быть частью кулинарной сети.
              </p>
              <p className={styles.textItem}>
                Присоединяйтесь к нам, создавайте, делитесь и вдохновляйтесь! Фудграм станет неотъемлемой
                частью вашего кулинарного опыта!
              </p>
            </div>
          </div>

          <aside>
            <h2 className={styles.additionalTitle}>Ссылки</h2>
            <div className={styles.text}>
              <p className={styles.textItem}>
                Код проекта находится тут -{' '}
                <a href="https://github.com/RockurDev" className={styles.textLink} target="_blank" rel="noopener noreferrer">
                  Github
                </a>
              </p>
              <p className={styles.textItem}>
                Автор проекта: <a href="https://github.com/RockurDev" className={styles.textLink} target="_blank" rel="noopener noreferrer">
                  Даниил Тропин (RockurDev)
                </a>
              </p>
            </div>
          </aside>
        </div>
      </Container>
    </Main>
  );
}

export default About
